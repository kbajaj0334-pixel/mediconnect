from django.db import models

# Create your models here.
class Hospital(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length= 50)
    state = models.CharField(max_length=50)
    phone_number = models.IntegerField()
    email = models.EmailField()

# class User(models.Model):
#     username = models.CharField(max_length=50)
#     password = models
#     email = models.EmailField()
    


# class Doctor(models.Model):
#     user_id =models.CharField(max_length= 50)



    def __str__(self):
        return self.title
    

# class doctor(models.Model):
#     Day = (
#         ('MONDAY', 'Monday'),
#         ('TUESDAY','Tuesday'),
#         ('WEDNESDAY','Wednesday'),
#         ('THURSDAY','Thursday'),
#         ('FRIDAY','Friday'),
#         ('SATURDAY', 'Saturday')
#     )
#     Booking = (
#         ('ONLINE', 'Online'),
#         ('OFFLINE','Offline')
#     )

#     Time = (
#         ('11:00 - 12:00','11:00 - 12:00'),
#         ('1:00 - 2:00', '1:00 - 2:00'),
#         ('3:00 - 4:00', '3:00 - 4:00'),
#         ('5:00 - 6:00', '5:00 - 6:00')
#     )
#     name = models.CharField(max_length=50)
#     fees = models.FloatField()
#     experience = models.TextField()
#     specialization = models.CharField(max_length=100)
#     img = models.ImageField(upload_to='course_img', blank=True , null=True)
#     days = models.CharField(max_length=50, choices=Day)
#     mode =  models.CharField(max_length=50, choices=Booking)


    def __str__(self):
        return self.name    