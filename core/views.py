from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
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

def hospital_doctors(request, hospital_id):
    hospital = get_object_or_404(Hospital, id=hospital_id)
    doctors = DoctorProfile.objects.filter(hospital=hospital, is_available=True)
    
    # Group doctors by specialization/department
    from collections import defaultdict
    doctors_by_specialization = defaultdict(list)
    for doctor in doctors:
        doctors_by_specialization[doctor.specialization].append(doctor)
        
    context = {
        'hospital': hospital,
        'doctors_by_specialization': dict(doctors_by_specialization),
    }
    return render(request, 'core/doctor_by_hospital.html', context)

from .models import Notification, ContactMessage
from django.contrib.auth.decorators import login_required

@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/notifications.html', {'notifications': notifications})


def about_us(request):
    context = {
        'mission': 'To make quality healthcare accessible by connecting patients with trusted doctors and hospitals.',
        'vision': 'A world where every person can find and book the right care in minutes.',
        'values': [
            ('Trust', 'Verified doctors and transparent hospital listings.'),
            ('Accessibility', 'Simple booking and records for every patient.'),
            ('Care', 'Patient-first design in everything we build.'),
        ],
        'stats': [
            ('500+', 'Partner doctors'),
            ('50+', 'Hospitals listed'),
            ('10,000+', 'Appointments booked'),
            ('24/7', 'Support availability'),
        ],
    }
    return render(request, 'core/about.html', context)


def contact_us(request):
    context = {
        'support_email': 'support@mediconnect.com',
        'phone': '+1 (555) 123-4567',
        'address': '123 Health Avenue, Suite 400, San Francisco, CA 94102',
        'hours': 'Monday – Friday, 9:00 AM – 6:00 PM (PST)',
        'form_data': {},
    }

    if request.user.is_authenticated:
        context['form_data'] = {
            'full_name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
        }

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message_text = request.POST.get('message', '').strip()

        context['form_data'] = {
            'full_name': full_name,
            'email': email,
            'subject': subject,
            'message': message_text,
        }

        if not full_name:
            messages.error(request, 'Please enter your full name.')
        elif not email:
            messages.error(request, 'Please enter your email address.')
        elif not subject:
            messages.error(request, 'Please enter a subject.')
        elif not message_text:
            messages.error(request, 'Please enter your message.')
        elif len(message_text) < 10:
            messages.error(request, 'Message must be at least 10 characters.')
        else:
            ContactMessage.objects.create(
                user=request.user if request.user.is_authenticated else None,
                full_name=full_name,
                email=email,
                subject=subject,
                message=message_text,
            )
            messages.success(request, 'Your message has been sent. We will get back to you soon.')
            return redirect('contact_us')

    return render(request, 'core/contact.html', context)


def privacy_policy(request):
    context = {
        'last_updated': 'May 1, 2026',
        'sections': [
            ('Information We Collect', 'We collect account details (name, email, role), appointment data, and optional profile information you provide when using Mediconnect.'),
            ('How We Use Your Data', 'Your data is used to manage appointments, display medical records to authorized users, send notifications, and improve our services.'),
            ('Data Sharing', 'We do not sell personal health information. Data may be shared with your chosen doctors and hospitals only as needed for care coordination.'),
            ('Security', 'We use industry-standard measures including encrypted connections and access controls to protect your information.'),
            ('Your Rights', 'You may request access, correction, or deletion of your account data by contacting support@mediconnect.com.'),
        ],
    }
    return render(request, 'core/privacy_policy.html', context)


def terms_of_service(request):
    context = {
        'last_updated': 'May 1, 2026',
        'sections': [
            ('Acceptance of Terms', 'By using Mediconnect you agree to these Terms of Service and our Privacy Policy.'),
            ('Use of the Platform', 'Mediconnect helps patients discover doctors and book appointments. It does not replace professional medical advice, diagnosis, or emergency care.'),
            ('User Accounts', 'You are responsible for keeping your login credentials secure and for activity under your account.'),
            ('Appointments', 'Appointment availability is set by doctors. Cancellations and rescheduling follow each provider\'s policies shown at booking time.'),
            ('Limitation of Liability', 'Mediconnect is provided "as is." We are not liable for medical outcomes; always seek emergency services when needed.'),
            ('Changes', 'We may update these terms. Continued use after changes constitutes acceptance of the revised terms.'),
        ],
    }
    return render(request, 'core/terms_of_service.html', context)
