from django.contrib import admin
from .models import Appointment, MedicalRecord

 
admin.site.register(Appointment)
admin.site.register(MedicalRecord)
