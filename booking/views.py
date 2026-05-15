from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.models import PatientProfile
from .models import Appointment, MedicalRecord

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
