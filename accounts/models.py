from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class User(AbstractUser):
    ROLE_CHOICES = (
        ('PATIENT', 'Patient'),
        ('DOCTOR', 'Doctor'),
        ('ADMIN', 'Admin'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True) 

class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20, blank=True)
    blood_group = models.CharField(max_length=10, blank=True)
    patient_pic = models.ImageField(upload_to='profiles/patients', blank=True, null=True)
    medical_history = models.TextField(blank=True)
    allergies = models.TextField(blank=True)

    def __str__(self):
        return self.user.username

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    hospital = models.ForeignKey('core.Hospital', on_delete=models.CASCADE)

    specialization = models.CharField(max_length=100)
    experience_years = models.IntegerField(default=0)
    doctor_pic = models.ImageField(upload_to='profiles/doctors', blank=True, null=True)
    fees_online = models.IntegerField(default=0)
    fees_offline = models.IntegerField(default=0)
    
    bio = models.TextField(blank=True)

    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username

class DoctorAvailability(models.Model):
    WEEKDAYS = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )

    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE
    )

    weekday = models.IntegerField(choices=WEEKDAYS)

    start_time = models.TimeField()
    end_time = models.TimeField()

    slot_duration = models.IntegerField(
        default=15,
        help_text="Duration in minutes"
    )

    is_active = models.BooleanField(default=True)

    class Meta:

        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    end_time__gt=models.F('start_time')
                ),
                name='availability_end_after_start'
            )
        ]

    def clean(self):

        super().clean()

        overlapping = DoctorAvailability.objects.filter(
            doctor=self.doctor,
            weekday=self.weekday,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            is_active=True
        )

        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)

        if overlapping.exists():
            raise ValidationError(
                "Availability overlaps with another schedule."
            )

    def save(self, *args, **kwargs):

        self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):

        return f"{self.doctor} - {self.get_weekday_display()}"