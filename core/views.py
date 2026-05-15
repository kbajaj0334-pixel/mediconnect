from django.shortcuts import render
from accounts.models import DoctorProfile, PatientProfile
from core.models import Hospital
from booking.models import Appointment
from django.utils import timezone

def home_view(request):
    context = {}
    if request.user.is_authenticated:
        if request.user.role == 'PATIENT':
            try:
                patient = PatientProfile.objects.get(user=request.user)
                context['upcoming_appointments'] = Appointment.objects.filter(
                    patient=patient,
                    appointment_date__gte=timezone.now().date(),
                    status__in=['PENDING', 'APPROVED']
                ).order_by('appointment_date', 'start_time')[:3]
            except PatientProfile.DoesNotExist:
                pass
        
        context['featured_doctors'] = DoctorProfile.objects.filter(is_available=True)[:4]
        context['hospitals'] = Hospital.objects.all()[:4]
    
    return render(request, 'core/home.html', context)

def hospital_list(request):
    hospitals = Hospital.objects.all()
    return render(request, 'core/hospital_list.html', {'hospitals': hospitals})

from .models import Notification
from django.contrib.auth.decorators import login_required

@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/notifications.html', {'notifications': notifications})
