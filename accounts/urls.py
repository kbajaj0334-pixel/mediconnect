from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/availability/', views.manage_availability, name='manage_availability'),
    path('doctors/find/', views.find_doctors, name='find_doctors'),
    path('profile/update/', views.update_profile_view, name='update_profile'),
    path('doctor/appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('doctor/patients/', views.doctor_patients, name='doctor_patients'),
    path('doctor/prescriptions/', views.doctor_prescriptions, name='doctor_prescriptions'),
    path('doctor/records/', views.doctor_records, name='doctor_records'),
    path('doctor/reports/', views.doctor_reports, name='doctor_reports'),
]
