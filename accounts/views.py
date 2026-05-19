from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import User, PatientProfile, DoctorProfile, DoctorAvailability
from core.models import Hospital

def register_view(request):
    if request.method == 'POST':
        # Manual data extraction (since no Django forms)
        role = request.POST.get('role')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')

        # Check if user exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return render(request, 'accounts/register.html', {'hospitals': Hospital.objects.all()})

        # Create User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            phone=phone
        )

        try:
            if role == 'PATIENT':
                PatientProfile.objects.create(
                    user=user,
                    date_of_birth=request.POST.get('date_of_birth'),
                    blood_group=request.POST.get('blood_group')
                )
            elif role == 'DOCTOR':
                hospital_id = request.POST.get('hospital')
                hospital = Hospital.objects.get(id=hospital_id)
                DoctorProfile.objects.create(
                    user=user,
                    hospital=hospital,
                    specialization=request.POST.get('specialization'),
                    experience_years=request.POST.get('experience_years', 0)
                )
            
            messages.success(request, 'Account created successfully!')
            login(request, user)
            return redirect('home') 
        except Exception as e:
            user.delete() 
            messages.error(request, f'Error creating profile: {str(e)}')
            return render(request, 'accounts/register.html', {'hospitals': Hospital.objects.all()})

    hospitals = Hospital.objects.all()
    return render(request, 'accounts/register.html', {'hospitals': hospitals})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            if user.role == 'DOCTOR':
                return redirect('doctor_dashboard')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'Logged out successfully')
    return redirect('login')

from django.contrib.auth.decorators import login_required

@login_required
def doctor_dashboard(request):
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied')
        return redirect('home')
    
    doctor = DoctorProfile.objects.get(user=request.user)
    from core.models import Notification
    
    if request.method == 'POST':
        notif_id = request.POST.get('notification_id')
        if notif_id:
            try:
                notif = Notification.objects.get(id=notif_id, user=request.user)
                notif.is_read = True
                notif.save()
                messages.success(request, 'Notification marked as read.')
            except Notification.DoesNotExist:
                pass
        return redirect('doctor_dashboard')
    
    from booking.models import Appointment
    from datetime import date
    
    today = date.today()
    today_appointments = Appointment.objects.filter(doctor=doctor, appointment_date=today).order_by('start_time')
    total_patients = Appointment.objects.filter(doctor=doctor).values('patient').distinct().count()
    
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    
    # Context
    context = {
        'doctor': doctor,
        'today_appointments': today_appointments,
        'total_patients': total_patients,
        'notifications': notifications,
    }
    
    return render(request, 'accounts/doctor_dashboard.html', context)

@login_required
def manage_availability(request):
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied')
        return redirect('home')
    
    doctor = DoctorProfile.objects.get(user=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'delete':
            slot_id = request.POST.get('slot_id')
            try:
                slot = DoctorAvailability.objects.get(id=slot_id, doctor=doctor)
                slot.delete()
                messages.success(request, 'Time slot deleted')
            except DoctorAvailability.DoesNotExist:
                messages.error(request, 'Slot not found')
        else:
            # Handle save/update
            slot_id = request.POST.get('slot_id')
            weekday = request.POST.get('weekday')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            slot_duration = request.POST.get('slot_duration', 15)
            
            try:
                if slot_id:
                    # Update existing
                    availability = DoctorAvailability.objects.get(id=slot_id, doctor=doctor)
                    availability.weekday = weekday
                    availability.start_time = start_time
                    availability.end_time = end_time
                    availability.slot_duration = slot_duration
                    availability.save()
                    messages.success(request, 'Availability updated successfully')
                else:
                    # Create new
                    DoctorAvailability.objects.create(
                        doctor=doctor,
                        weekday=weekday,
                        start_time=start_time,
                        end_time=end_time,
                        slot_duration=slot_duration
                    )
                    messages.success(request, 'Availability added successfully')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
            
        return redirect('manage_availability')

    availabilities = DoctorAvailability.objects.filter(doctor=doctor).order_by('weekday', 'start_time')
    
    # Group availabilities by weekday
    avail_dict = {i: [] for i, _ in DoctorAvailability.WEEKDAYS}
    for a in availabilities:
        avail_dict[a.weekday].append(a)
        
    days_data = []
    for i, name in DoctorAvailability.WEEKDAYS:
        days_data.append({
            'id': i,
            'name': name,
            'slots': avail_dict.get(i, []),
            'has_data': len(avail_dict.get(i, [])) > 0
        })

    return render(request, 'accounts/manage_availability.html', {
        'doctor': doctor,
        'days_data': days_data
    })

@login_required
def find_doctors(request):
    specialization = request.GET.get('specialization')
    if specialization:
        doctors = DoctorProfile.objects.filter(specialization__icontains=specialization, is_available=True)
    else:
        doctors = DoctorProfile.objects.filter(is_available=True)
    
    return render(request, 'accounts/find_doctors.html', {'doctors': doctors})

@login_required
def update_profile_view(request):
    user = request.user
    hospitals = Hospital.objects.all()
    profile = None
    
    if user.role == 'PATIENT':
        try:
            profile = PatientProfile.objects.get(user=user)
        except PatientProfile.DoesNotExist:
            # Handle case where profile wasn't created during registration
            profile = PatientProfile.objects.create(user=user, date_of_birth='2000-01-01')
            
        if request.method == 'POST':
            profile.date_of_birth = request.POST.get('date_of_birth')
            profile.gender = request.POST.get('gender')
            profile.blood_group = request.POST.get('blood_group')
            profile.medical_history = request.POST.get('medical_history')
            profile.allergies = request.POST.get('allergies')
            
            if 'patient_pic' in request.FILES:
                profile.patient_pic = request.FILES['patient_pic']
            
            profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('home')
            
    elif user.role == 'DOCTOR':
        try:
            profile = DoctorProfile.objects.get(user=user)
        except DoctorProfile.DoesNotExist:
            messages.error(request, 'Doctor profile not found.')
            return redirect('doctor_dashboard')

        if request.method == 'POST':
            hospital_id = request.POST.get('hospital')
            if hospital_id:
                try:
                    profile.hospital = Hospital.objects.get(id=hospital_id)
                except Hospital.DoesNotExist:
                    pass
            
            profile.specialization = request.POST.get('specialization')
            profile.experience_years = int(request.POST.get('experience_years', 0) or 0)
            profile.fees_online = int(request.POST.get('fees_online', 0) or 0)
            profile.fees_offline = int(request.POST.get('fees_offline', 0) or 0)
            profile.bio = request.POST.get('bio')
            profile.is_available = 'is_available' in request.POST
            
            if 'doctor_pic' in request.FILES:
                profile.doctor_pic = request.FILES['doctor_pic']
            
            profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('doctor_dashboard')
    
    context = {
        'profile': profile,
        'hospitals': hospitals,
        'role': user.role
    }
    
    if user.role == 'DOCTOR':
        return render(request, 'accounts/doctor_profile.html', context)
    return render(request, 'accounts/updateprofile.html', context)

@login_required
def doctor_appointments(request):
    if request.user.role != 'DOCTOR':
        return redirect('home')
    doctor = DoctorProfile.objects.get(user=request.user)
    from booking.models import Appointment
    
    if request.method == 'POST':
        appt_id = request.POST.get('appointment_id')
        new_status = request.POST.get('status')
        if appt_id and new_status in dict(Appointment.STATUS_CHOICES):
            try:
                appt = Appointment.objects.get(id=appt_id, doctor=doctor)
                appt.status = new_status
                appt.save()
                messages.success(request, f'Appointment status updated to {new_status}')
            except Appointment.DoesNotExist:
                messages.error(request, 'Appointment not found.')
        return redirect('doctor_appointments')

    appointments = Appointment.objects.filter(doctor=doctor).order_by('-appointment_date', '-start_time')
    return render(request, 'accounts/doctor_appointments.html', {'doctor': doctor, 'appointments': appointments})

@login_required
def doctor_patients(request):
    if request.user.role != 'DOCTOR':
        return redirect('home')
    doctor = DoctorProfile.objects.get(user=request.user)
    from booking.models import Appointment
    from accounts.models import PatientProfile
    
    patient_ids = Appointment.objects.filter(doctor=doctor, status='COMPLETED').values_list('patient', flat=True).distinct()
    patients = PatientProfile.objects.filter(id__in=patient_ids)
    
    return render(request, 'accounts/doctor_patients.html', {'doctor': doctor, 'patients': patients})

@login_required
def doctor_prescriptions(request):
    if request.user.role != 'DOCTOR':
        return redirect('home')
    doctor = DoctorProfile.objects.get(user=request.user)
    from booking.models import MedicalRecord, Appointment
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create' or action == 'update':
            appt_id = request.POST.get('appointment_id')
            prescription = request.POST.get('prescription')
            diagnosis = request.POST.get('diagnosis')
            try:
                appt = Appointment.objects.get(id=appt_id, doctor=doctor)
                record, created = MedicalRecord.objects.get_or_create(appointment=appt)
                record.prescription = prescription
                record.diagnosis = diagnosis
                record.save()
                messages.success(request, 'Prescription saved successfully.')
            except Appointment.DoesNotExist:
                messages.error(request, 'Invalid appointment.')
        elif action == 'delete':
            record_id = request.POST.get('record_id')
            try:
                record = MedicalRecord.objects.get(id=record_id, appointment__doctor=doctor)
                record.prescription = '' # Or delete the record completely if you want: record.delete()
                record.save()
                messages.success(request, 'Prescription deleted.')
            except MedicalRecord.DoesNotExist:
                messages.error(request, 'Record not found.')
        return redirect('doctor_prescriptions')

    records = MedicalRecord.objects.filter(appointment__doctor=doctor).exclude(prescription='').order_by('-created_at')
    # Also fetch completed appointments without prescriptions to allow creating new ones
    appointments = Appointment.objects.filter(doctor=doctor, status='COMPLETED', medicalrecord__isnull=True)
    return render(request, 'accounts/doctor_prescriptions.html', {'doctor': doctor, 'records': records, 'appointments': appointments})

@login_required
def doctor_records(request):
    if request.user.role != 'DOCTOR':
        return redirect('home')
    doctor = DoctorProfile.objects.get(user=request.user)
    from booking.models import MedicalRecord
    records = MedicalRecord.objects.filter(appointment__doctor=doctor).order_by('-created_at')
    return render(request, 'accounts/doctor_records.html', {'doctor': doctor, 'records': records})

@login_required
def doctor_reports(request):
    if request.user.role != 'DOCTOR':
        return redirect('home')
    doctor = DoctorProfile.objects.get(user=request.user)
    return render(request, 'accounts/doctor_reports.html', {'doctor': doctor})
