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
            records = MedicalRecord.objects.filter(appointment__patient=patient).order_by('-created_at')
        except PatientProfile.DoesNotExist:
            records = []
    else:
        # For doctors, maybe show records of their patients?
        records = []
        
    return render(request, 'booking/medical_records.html', {'records': records})

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
        else:
            appointment.severity_score = 0
            appointment.severity_level = 'LOW'

        try:
            appointment.full_clean()
            appointment.save()
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
