from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import date
from accounts.models import DoctorAvailability

class Appointment(models.Model):

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('MISSED', 'Missed'),
        ('RESCHEDULE', 'Reschedule')
    )

    SEVERITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    )

    CONSULTATION_CHOICES = (
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline'),
    )

    patient = models.ForeignKey('accounts.PatientProfile',on_delete=models.CASCADE)
    doctor = models.ForeignKey('accounts.DoctorProfile',on_delete=models.CASCADE)
    hospital = models.ForeignKey('core.Hospital',on_delete=models.CASCADE)

    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    consultation_mode = models.CharField(max_length=20,choices=CONSULTATION_CHOICES)
    symptoms = models.TextField(blank=True)
    # pain_level = models.IntegerField(
    #     default=1,
    #     validators=[
    #         MinValueValidator(1),
    #         MaxValueValidator(10)
    #     ]
    # )

    severity_score = models.IntegerField(default=0)
    severity_level = models.CharField(max_length=20,choices=SEVERITY_CHOICES,default='LOW')

    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='PENDING')
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    booked_at = models.DateTimeField(auto_now_add=True)
    reminder_sent = models.BooleanField(default=False)


    def clean(self):
        super().clean()
      
        if self.start_time >= self.end_time:
            raise ValidationError({
                'end_time': 'End time must be greater than start time.'
            })

        overlapping = Appointment.objects.filter(
            doctor=self.doctor,
            appointment_date=self.appointment_date,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            status__in=['PENDING', 'APPROVED']
        )

        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)

        if overlapping.exists():
            raise ValidationError(
                "This slot is already booked."
            )
        
        weekday = self.appointment_date.weekday()

        available = DoctorAvailability.objects.filter(
            doctor=self.doctor,
            weekday=weekday,
            start_time__lte=self.start_time,
            end_time__gte=self.end_time,
            is_active=True
        ).exists()

        if not available:
            raise ValidationError(
                "Doctor is not available at this time."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        if self.consultation_mode == 'ONLINE':
            from django.utils import timezone
            from datetime import datetime
            import uuid

            naive_start = datetime.combine(self.appointment_date, self.start_time)
            naive_end = datetime.combine(self.appointment_date, self.end_time)
            aware_start = timezone.make_aware(naive_start)
            aware_end = timezone.make_aware(naive_end)

            meeting, created = OnlineMeeting.objects.get_or_create(
                appointment=self,
                defaults={
                    'room_name': f"MediConnect-{uuid.uuid4().hex[:16]}",
                    'meeting_link': '',
                    'start_time': aware_start,
                    'end_time': aware_end,
                }
            )
            if created or meeting.start_time != aware_start or meeting.end_time != aware_end:
                if not meeting.room_name:
                    meeting.room_name = f"MediConnect-{uuid.uuid4().hex[:16]}"
                meeting.meeting_link = f"https://meet.jit.si/{meeting.room_name}"
                meeting.start_time = aware_start
                meeting.end_time = aware_end
                meeting.save()
        else:
            OnlineMeeting.objects.filter(appointment=self).delete()

    def __str__(self):
        return f"{self.patient} -> {self.doctor}"
 
class MedicalRecord(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE)
    diagnosis = models.TextField(blank=True)
    prescription = models.TextField(blank=True)
    file = models.FileField(upload_to='media/records/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.appointment.patient} -> {self.appointment.doctor}"

class OnlineMeeting(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='online_meeting')
    room_name = models.CharField(max_length=255, unique=True)
    meeting_link = models.URLField(max_length=500)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Meeting link: {self.meeting_link}"