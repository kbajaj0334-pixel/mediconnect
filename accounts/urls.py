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
]
