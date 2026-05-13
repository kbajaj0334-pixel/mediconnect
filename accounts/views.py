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
    return render(request, 'accounts/doctor_dashboard.html', {'doctor': doctor})

@login_required
def manage_availability(request):
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied')
        return redirect('home')
    
    doctor = DoctorProfile.objects.get(user=request.user)
    
    if request.method == 'POST':
        # Handle form submission for availability
        weekday = request.POST.get('weekday')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        slot_duration = request.POST.get('slot_duration', 15)
        
        try:
            availability, created = DoctorAvailability.objects.update_or_create(
                doctor=doctor,
                weekday=weekday,
                defaults={
                    'start_time': start_time,
                    'end_time': end_time,
                    'slot_duration': slot_duration,
                    'is_active': True
                }
            )
            messages.success(request, 'Availability updated successfully')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            
        return redirect('manage_availability')

    availabilities = DoctorAvailability.objects.filter(doctor=doctor).order_by('weekday')
    # Pre-fill a list of 7 days
    days_data = []
    avail_dict = {a.weekday: a for a in availabilities}
    for i, name in DoctorAvailability.WEEKDAYS:
        days_data.append({
            'id': i,
            'name': name,
            'avail': avail_dict.get(i)
        })

    return render(request, 'accounts/manage_availability.html', {
        'doctor': doctor,
        'days_data': days_data
    })
