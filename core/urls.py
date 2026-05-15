from django.urls import path
from . import views

urlpatterns = [
    path('hospitals/', views.hospital_list, name='hospital_list'),
    path('notifications/', views.notifications, name='notifications'),
]
