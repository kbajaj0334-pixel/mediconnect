from django.urls import path
from . import views

urlpatterns = [
    path('',  views.login, name='login'),
    path('about/',  views.about, name='about'),
    path('home/',  views.home, name='home'),
    path('hospital/', views.hospital_profile, name= 'hospital_profile'),
    path('index/',  views.index, name='index'),
    path('logout/',  views.about, name='logout'),
    path('login/',  views.login, name='login'),
    path('doctor_dashboard/',  views.doctor_dashboard, name='doctor_dashboard'),
    path('patient_dashboard/',  views.patient_dashboard, name='patient_dashboard'),
    path('patient_register/',  views.patient_register, name='patient_register'),
    path('doctor_register/',  views.doctor_register, name='doctor_register'),


]