from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Appointment, MedicalRecord
from accounts.models import PatientProfile, DoctorProfile, DoctorAvailability
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.contrib import messages
from .utils import calculate_severity

@login_required
def medical_records(request):
    if request.user.role == 'PATIENT':
        try:
            patient = PatientProfile.objects.get(user=request.user)
            appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_date', '-start_time')
        except PatientProfile.DoesNotExist:
            patient = None
            appointments = []
    else:
        patient = None
        appointments = []
        
    return render(request, 'booking/medical_records.html', {
        'patient': patient,
        'appointments': appointments
    })

@login_required
def book_appointment(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    
    if request.user.role != 'PATIENT':
        messages.error(request, 'Only patients can book appointments.')
        return redirect('home')
        
    if request.method == 'POST':
        date_str = request.POST.get('date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        mode = request.POST.get('consultation_mode')
        
        is_emergency = request.POST.get('is_emergency') == 'on'
        symptoms = request.POST.getlist('symptoms')
        pain_level = int(request.POST.get('pain_level', 1))
        
        try:
            patient = request.user.patientprofile
        except PatientProfile.DoesNotExist:
            messages.error(request, 'Patient profile not found.')
            return redirect('home')

        try:
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if not is_emergency or (start_time_str and end_time_str):
                start_time = datetime.strptime(start_time_str, '%H:%M').time()
                end_time = datetime.strptime(end_time_str, '%H:%M').time()
            else:
                # Auto-assign slot
                weekday = appointment_date.weekday()
                availabilities = DoctorAvailability.objects.filter(doctor=doctor, weekday=weekday, is_active=True)
                booked_appointments = Appointment.objects.filter(
                    doctor=doctor, appointment_date=appointment_date, status__in=['PENDING', 'APPROVED']
                )
                
                auto_start, auto_end = None, None
                for avail in availabilities:
                    current_time = datetime.combine(appointment_date, avail.start_time)
                    end_time_avail = datetime.combine(appointment_date, avail.end_time)
                    
                    while current_time + timedelta(minutes=avail.slot_duration) <= end_time_avail:
                        slot_end = current_time + timedelta(minutes=avail.slot_duration)
                        
                        is_booked = booked_appointments.filter(
                            start_time__lt=slot_end.time(),
                            end_time__gt=current_time.time()
                        ).exists()
                        
                        if not is_booked:
                            auto_start = current_time.time()
                            auto_end = slot_end.time()
                            break
                        current_time = slot_end
                    if auto_start:
                        break
                
                if auto_start and auto_end:
                    start_time = auto_start
                    end_time = auto_end
                else:
                    messages.error(request, 'No available slots found for emergency assignment on this date.')
                    return redirect('book_appointment', doctor_id=doctor.id)
                    
        except (ValueError, TypeError):
            messages.error(request, 'Invalid date or time.')
            return redirect('book_appointment', doctor_id=doctor.id)

        appointment = Appointment(
            patient=patient,
            doctor=doctor,
            hospital=doctor.hospital,
            appointment_date=appointment_date,
            start_time=start_time,
            end_time=end_time,
            consultation_mode=mode,
            symptoms=", ".join(symptoms) if is_emergency else "",
            pain_level=pain_level if is_emergency else 1,
        )

        if is_emergency:
            severity_data = calculate_severity(pain_level, symptoms, patient)
            appointment.severity_score = severity_data['score']
            appointment.severity_level = severity_data['severity_level']
            
            if appointment.severity_level == 'CRITICAL' or appointment.severity_level == 'MEDIUM':
                appointment.status = 'APPROVED'
        else:
            appointment.severity_score = 0
            appointment.severity_level = 'LOW'

        try:
            appointment.full_clean()
            appointment.save()
            
            if appointment.severity_level == 'CRITICAL':
                from core.models import Notification
                from django.core.mail import send_mail
                from django.conf import settings
                
                Notification.objects.create(
                    user=doctor.user,
                    message=f"CRITICAL EMERGENCY: Patient {patient.user.username} booked an appointment on {appointment.appointment_date} at {appointment.start_time}."
                )
                send_mail(
                    subject='CRITICAL EMERGENCY APPOINTMENT',
                    message=f"CRITICAL EMERGENCY: Patient {patient.user.username} booked an appointment on {appointment.appointment_date} at {appointment.start_time}.\nSymptoms: {appointment.symptoms}",
                    from_email=settings.EMAIL_HOST_USER if hasattr(settings, 'EMAIL_HOST_USER') else None,
                    recipient_list=[doctor.user.email],
                    fail_silently=True,
                )
                messages.error(request, 'CRITICAL emergency recorded. Appointment auto-approved and doctor notified immediately.')
            elif appointment.severity_level == 'HIGH':
                from core.models import Notification
                Notification.objects.create(
                    user=doctor.user,
                    message=f"HIGH PRIORITY: Patient {patient.user.username} booked an appointment on {appointment.appointment_date} at {appointment.start_time}."
                )
                messages.warning(request, 'High severity recorded. Doctor has been notified.')
            elif appointment.severity_level == 'MEDIUM':
                messages.info(request, 'Medium severity recorded. Appointment automatically approved.')
            else:
                messages.success(request, 'Appointment booked successfully!')

            return redirect('home')
        except Exception as e:
            messages.error(request, f'Error booking appointment: {e}')
            return redirect('book_appointment', doctor_id=doctor.id)

    return render(request, 'booking/book_appointment.html', {'doctor': doctor})

@login_required
def get_available_slots(request, doctor_id, date):
    try:
        req_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    weekday = req_date.weekday()
    
    availabilities = DoctorAvailability.objects.filter(doctor=doctor, weekday=weekday, is_active=True)
    
    booked_appointments = Appointment.objects.filter(
        doctor=doctor, appointment_date=req_date, status__in=['PENDING', 'APPROVED']
    )
    
    slots = []
    for avail in availabilities:
        current_time = datetime.combine(req_date, avail.start_time)
        end_time = datetime.combine(req_date, avail.end_time)
        
        while current_time + timedelta(minutes=avail.slot_duration) <= end_time:
            slot_end = current_time + timedelta(minutes=avail.slot_duration)
            
            is_booked = booked_appointments.filter(
                start_time__lt=slot_end.time(),
                end_time__gt=current_time.time()
            ).exists()
            
            if not is_booked:
                slots.append({
                    'start_time': current_time.time().strftime('%H:%M'),
                    'end_time': slot_end.time().strftime('%H:%M')
                })
            
            current_time = slot_end
            
    return JsonResponse({'slots': slots})

@login_required
def appointment_detail(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check authorization: user must be the patient or the doctor of the appointment
    if request.user.role == 'PATIENT':
        try:
            patient = request.user.patientprofile
            if appointment.patient != patient:
                messages.error(request, 'You are not authorized to view this appointment.')
                return redirect('home')
        except PatientProfile.DoesNotExist:
            messages.error(request, 'Patient profile not found.')
            return redirect('home')
    elif request.user.role == 'DOCTOR':
        try:
            doctor = request.user.doctorprofile
            if appointment.doctor != doctor:
                messages.error(request, 'You are not authorized to view this appointment.')
                return redirect('home')
        except DoctorProfile.DoesNotExist:
            messages.error(request, 'Doctor profile not found.')
            return redirect('home')
    else:
        messages.error(request, 'Access denied.')
        return redirect('home')

    return render(request, 'booking/appointment_detail.html', {'appointment': appointment})

@login_required
def reschedule_closest_slot(request, appointment_id):
    from django.utils import timezone
    from datetime import timezone as py_timezone, timedelta
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check authorization: user must be the patient of this appointment
    if request.user.role != 'PATIENT':
        return JsonResponse({'error': 'Only patients can reschedule.'}, status=403)
        
    try:
        patient = request.user.patientprofile
        if appointment.patient != patient:
            return JsonResponse({'error': 'Unauthorized.'}, status=403)
    except PatientProfile.DoesNotExist:
        return JsonResponse({'error': 'Patient profile not found.'}, status=404)
        
    # Check if severity is High or Critical
    if appointment.severity_level not in ['HIGH', 'CRITICAL']:
        return JsonResponse({'error': 'Rescheduling to closest slot is only allowed for High or Critical severity level.'}, status=400)
        
    doctor = appointment.doctor
    
    # Use Indian Standard Time (IST = UTC + 5:30)
    ist_tz = py_timezone(timedelta(hours=5, minutes=30))
    current_datetime = timezone.now().astimezone(ist_tz)
    found_slot = None
    
    # Look for the closest slot within the next 30 days
    for day_offset in range(30):
        search_date = current_datetime.date() + timedelta(days=day_offset)
        weekday = search_date.weekday()
        
        # Get active availability for the doctor on this weekday
        availabilities = DoctorAvailability.objects.filter(
            doctor=doctor, weekday=weekday, is_active=True
        ).order_by('start_time')
        
        # Fetch existing appointments for this doctor on this search date
        booked_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=search_date,
            status__in=['PENDING', 'APPROVED']
        )
        
        for avail in availabilities:
            slot_start_dt = datetime.combine(search_date, avail.start_time)
            slot_end_dt = datetime.combine(search_date, avail.end_time)
            slot_duration = timedelta(minutes=avail.slot_duration)
            
            curr_slot_start = slot_start_dt
            while curr_slot_start + slot_duration <= slot_end_dt:
                curr_slot_end = curr_slot_start + slot_duration
                
                # If search date is today, make sure the slot start time is in the future
                if search_date == current_datetime.date():
                    if curr_slot_start.time() <= current_datetime.time():
                        curr_slot_start = curr_slot_end
                        continue
                
                # Check if this slot overlaps with any booked appointments (excluding this one)
                overlap = booked_appointments.filter(
                    start_time__lt=curr_slot_end.time(),
                    end_time__gt=curr_slot_start.time()
                )
                if appointment.pk:
                    overlap = overlap.exclude(pk=appointment.pk)
                    
                if not overlap.exists():
                    found_slot = {
                        'date': search_date,
                        'start_time': curr_slot_start.time(),
                        'end_time': curr_slot_end.time()
                    }
                    break
                    
                curr_slot_start = curr_slot_end
            if found_slot:
                break
        if found_slot:
            break
            
    if found_slot:
        appointment.appointment_date = found_slot['date']
        appointment.start_time = found_slot['start_time']
        appointment.end_time = found_slot['end_time']
        appointment.status = 'APPROVED'
        
        try:
            appointment.full_clean()
            appointment.save()
            messages.success(
                request,
                f"Appointment rescheduled to closest slot: {found_slot['date'].strftime('%A, %b %d')} at {found_slot['start_time'].strftime('%H:%M')}."
            )
            return JsonResponse({
                'success': True,
                'new_date': found_slot['date'].strftime('%Y-%m-%d'),
                'new_start_time': found_slot['start_time'].strftime('%H:%M'),
                'new_end_time': found_slot['end_time'].strftime('%H:%M')
            })
        except Exception as e:
            return JsonResponse({'error': f"Rescheduling failed: {e}"}, status=400)
    else:
        return JsonResponse({'error': 'No available slots found in the next 30 days.'}, status=404)
