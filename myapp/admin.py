from django.contrib import admin
from .models import Hospital ,User , Patient, Doctor, Doctor_Availablity, Appointment, TimeSlot

# Register your models here.
admin.site.register(Hospital)
admin.site.register(User)
admin.site.register(Patient)
admin.site.register(Doctor)
admin.site.register(Doctor_Availablity)
admin.site.register(Appointment)
admin.site.register(TimeSlot)

