from django.db import models

# Create your models here.
class Hospital(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length= 50)
    state = models.CharField(max_length=50)
    phone_number = models.IntegerField()
    email = models.EmailField()

    def __str__(self):
        return self.name

class User(models.Model):
    CHOICES = (
        ('DOCTOR', 'Doctor'),
        ('PATIENT', 'Patient')
    )
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=100)
    name = models.CharField(max_length=50, default="abc")
    email = models.EmailField(unique = True)
    role = models.CharField(max_length=50, choices=CHOICES)
    password = models.CharField(max_length=50)
    DOB = models.DateField()
    phone_number = models.IntegerField()

    def __str__(self):
        return self.username
        

class Patient(models.Model):
    GENDER = (
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHERS', 'others')
    )
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models. CASCADE)
    age = models.IntegerField()
    gender = models.CharField(max_length=50, choices= GENDER)
    blood_group = models.CharField(max_length=50)
    medical_history = models.FileField(upload_to='medical_file/', blank=True, null=True)

    def __str__(self):
        return self.user_id.name  

class Doctor(models.Model):
    MODE =(
        ('ONLINE', 'online'),
        ('OFFLINE', 'offline')
    )
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models. CASCADE)
    hospital_id = models.ForeignKey(Hospital, on_delete=models. CASCADE)
    age = models.IntegerField()
    specialization = models.CharField(max_length=100)
    experience_years = models.CharField(max_length=50)
    fees = models.CharField(max_length=50, choices = MODE)
    bio = models.CharField(max_length=100)
    
    def __str__(self):
        return self.user_id.name 
     
class Doctor_Availablity(models.Model):
    AVAILABLITY = (
        ('ONLINE', 'online'),
        ('OFFLINE', 'offline')
    )

    doctor_availablity = models.CharField(max_length=50, choices = AVAILABLITY )

    def __str__(self):
        return self.doctor_availablity

class Appointment(models.Model):
    STATUS = (
        ('PENDING', 'pending'),
        ('APPROVED', 'approved'),
        ('REJECTED', 'rejected'),
    )
    SEVERITY_LEVEL = (
        ('MINOR PROBLEM', 'minor problem'),
        ('MODERATE PROBLEM', 'moderate problem'),
        ('SERIOUS PROBLEM', 'serious problem'),
    )
    PAIN_LEVEL = (
        ('NO PAIN','no pain'),
        ('MILD PAIN','mild pain'),
        ('MODERATE PAIN','moderate pain'),
        ('SEVERE PAIN','severe pain'),
        ('WORST PAIN','worst pain'),
    )
    id = models.AutoField(primary_key=True)
    Patient_id = models.ForeignKey(Patient, on_delete=models. CASCADE)
    Doctor_id = models.ForeignKey(Doctor, on_delete=models. CASCADE)
    Hospital_id = models.ForeignKey(Hospital, on_delete=models. CASCADE)
    TimeSlot_id = models.ForeignKey('TimeSlot', on_delete=models. CASCADE)
    status = models.CharField(max_length=50,choices=STATUS)
    symptoms = models.TextField()
    pain_level= models.CharField(max_length=50,choices=PAIN_LEVEL,null=True,blank=True)
    severity_level = models.CharField(max_length=50,choices=SEVERITY_LEVEL)

    def __str__(self):
        return self.Patient_id.user_id.name

    

class TimeSlot(models.Model):
    id = models.AutoField(primary_key=True)
    Patient_id = models.ForeignKey(Patient, on_delete=models. CASCADE)
    doctor_id = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField()

    def __str__(self):
        return self.Patient_id.name

     