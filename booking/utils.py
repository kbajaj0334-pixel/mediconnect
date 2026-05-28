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


from datetime import date


def calculate_severity(symptoms,patient):
    # 1. Base Pain Score
    # score = pain_level * 5
    score=1

    # 2. Symptom Weights
    symptom_weights = {
        "chest_pain": 25,
        "breathing_difficulty": 20,
        "high_fever": 15,
        "vomiting": 10,
        "dizziness": 8,
        "fatigue": 5,
    }

    for symptom in symptoms:
        if symptom in symptom_weights:
            score += symptom_weights[symptom]

    # 3. Risk Detection
    risk_keywords = [
        "diabetes",
        "hypertension",
        "heart",
        "cardiac",
        "asthma",
        "cancer",
        "bp",
        "kidney",
    ]

    history_text = (f"{patient.medical_history} "f"{patient.allergies}").lower()
    has_risk = any(keyword in history_text for keyword in risk_keywords)

    if has_risk:
        score *= 1.2

    # 4. Age Factor
    today = date.today()
    age = ( today.year - patient.date_of_birth.year - ( (today.month, today.day)<  (  patient.date_of_birth.month,  patient.date_of_birth.day  )  ))

    if age > 60 or age < 5:
        score += 10

    # 5. Cap Score
    score = min(round(score), 100)

    # 6. Severity Classification
    if score >= 75:
        level = "CRITICAL"
        badge = "Red Badge"
        slot = "Auto-assigned FIRST available slot"
        doctor_alert = "Red Badge + Emergency Flag"
    elif score >= 50:
        level = "HIGH"
        badge = "Orange Badge"
        slot = "Auto-assigned within 24 hours"
        doctor_alert = "Orange Badge + Priority Flag"
    elif score >= 25:
        level = "MEDIUM"
        badge = "Yellow Badge"
        slot = "Choose from next 3 days slots"
        doctor_alert = "Yellow Badge"

    else:
        level = "LOW"
        badge = "Green Badge"
        slot = "Choose any available slot"
        doctor_alert = "Green Badge"

    return {
        "score": score,
        "severity_level": level,
        "badge": badge,
        "slot_allocation": slot,
        "doctor_alert": doctor_alert,
        "risk_detected": has_risk,
    }