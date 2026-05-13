from datetime import datetime, timedelta
from django.utils import timezone
from accounts.models import DoctorAvailability
 
def is_slot_overlapping(existing_start, existing_end, new_start, new_end):
    """
    Check if a new time slot overlaps with an existing time slot.
    """
    return (new_start < existing_end) and (new_end > existing_start)

def get_available_slots(doctor, hospital, date):
    
    # Get all doctor availability records for this doctor and hospital on this date
    availability_records = DoctorAvailability.objects.filter(
        doctor=doctor,
        hospital=hospital,
        date=date,
    )
    
    # If no availability records, return empty list
    if not availability_records:
        return []
    
    # Get all existing appointments for this doctor and hospital on this date
    existing_appointments = Appointment.objects.filter(
        doctor=doctor,
        hospital=hospital,
        appointment_date=date,
        status__in=['APPROVED', 'COMPLETED'],
    )
    
    # Generate available slots based on availability records and existing appointments
    available_slots = []
    
    for availability in availability_records:
        start_time = availability.start_time
        end_time = availability.end_time
        
        # Check for overlaps with existing appointments
        for appointment in existing_appointments:
            if is_slot_overlapping(
                start_time,
                end_time,
                appointment.start_time,
                appointment.end_time,
            ):
                # If overlap found, adjust the available time slot
                if appointment.start_time < start_time:
                    end_time = appointment.start_time
                if appointment.end_time > end_time:
                    start_time = appointment.end_time
        
        # If valid slot remaining, add to available slots
        if start_time < end_time:
            available_slots.append({
                'start_time': start_time,
                'end_time': end_time,
            })
    
    return available_slots