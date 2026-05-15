from django.urls import path
from . import views

urlpatterns = [
    path('records/', views.medical_records, name='medical_records'),
]
