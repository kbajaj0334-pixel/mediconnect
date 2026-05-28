from django.contrib import admin
from .models import Appointment, MedicalRecord, OnlineMeeting

 
admin.site.register(Appointment)
admin.site.register(MedicalRecord)
admin.site.register(OnlineMeeting)
