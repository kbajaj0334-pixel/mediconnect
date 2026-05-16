from django.urls import path
from . import views

urlpatterns = [
    path('records/', views.medical_records, name='medical_records'),
    path('book/<int:doctor_id>/', views.book_appointment, name='book_appointment'),
    path('api/available-slots/<int:doctor_id>/<str:date>/', views.get_available_slots, name='get_available_slots'),
]
