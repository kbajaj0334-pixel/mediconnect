from django.urls import path
from . import views

urlpatterns = [
    path('hospitals/', views.hospital_list, name='hospital_list'),
    path('hospitals/<int:hospital_id>/doctors/', views.hospital_doctors, name='hospital_doctors'),
    path('notifications/', views.notifications, name='notifications'),
    path('about/', views.about_us, name='about_us'),
    path('contact/', views.contact_us, name='contact_us'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
]
