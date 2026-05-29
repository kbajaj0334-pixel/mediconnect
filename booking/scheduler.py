import logging
import sys
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

def send_appointment_reminders():
    """
    Sends email reminders to patients 2 minutes before their appointments start.
    """
    print("run")
    try:
        from booking.models import Appointment
        now = timezone.localtime()
        today = now.date()
        
        # Get all approved appointments for today or the future that haven't had reminders sent
        appointments = Appointment.objects.filter(
            status='APPROVED',
            appointment_date__gte=today,
            reminder_sent=False
        )
        
        for appt in appointments:
            try:
                print("trty")

                # Combine appointment date and start time
                naive_start = datetime.combine(appt.appointment_date, appt.start_time)
          
                aware_start = timezone.make_aware(naive_start)
        
                time_until_start = aware_start - now
              
                print(f"DEBUG: appt={appt.id}, now={now}, aware_start={aware_start}, diff={time_until_start}")
                
                # Check if the appointment starts in the next 2.5 minutes to catch it in the 30-second interval
                if timedelta(seconds=0) <= time_until_start <= timedelta(minutes=2, seconds=30):
                    patient_email = appt.patient.user.email
                    print("1 detct")
                    if patient_email:
                        print("detect")
                        
                        meeting_details = ""
                        if appt.consultation_mode == 'ONLINE':
                            try:
                                meeting = appt.online_meeting
                                meeting_details = f"Meeting Link: {meeting.meeting_link}\nRoom Name: {meeting.room_name}\n\n"
                            except Exception:
                                import uuid
                                from booking.models import OnlineMeeting
                                naive_start = datetime.combine(appt.appointment_date, appt.start_time)
                                naive_end = datetime.combine(appt.appointment_date, appt.end_time)
                                room_uuid = uuid.uuid4().hex[:16]
                                room_name = f"MediConnect-{room_uuid}"
                                meeting = OnlineMeeting.objects.create(
                                    appointment=appt,
                                    room_name=room_name,
                                    meeting_link=f"https://meet.jit.si/{room_name}",
                                    start_time=timezone.make_aware(naive_start),
                                    end_time=timezone.make_aware(naive_end)
                                )
                                meeting_details = f"Meeting Link: {meeting.meeting_link}\nRoom Name: {meeting.room_name}\n\n"

                        subject = f"Reminder: Your Appointment with Dr. {appt.doctor.user.username} starts in 2 minutes"
                        message = (
                            f"Dear {appt.patient.user.username},\n\n"
                            f"This is a reminder that your appointment with Dr. {appt.doctor.user.username} "
                            f"at {appt.hospital.name} is scheduled to start in 2 minutes "
                            f"(at {appt.start_time.strftime('%I:%M %p')}).\n\n"
                            f"Consultation Mode: {appt.get_consultation_mode_display()}\n"
                            f"{meeting_details}"
                            f"Date: {appt.appointment_date}\n\n"
                            f"Please make sure you are ready for your appointment.\n\n"
                            f"Best regards,\n"
                            f"MediConnect Team"
                        )
                        send_mail(
                            subject,
                            message,
                            settings.EMAIL_HOST_USER,
                            [patient_email],
                            fail_silently=False,
                        )
                        print("sent")
                        logger.info(f"Reminder email sent to {patient_email} for appointment ID {appt.id}")
                    
                    # Update status so reminder is not sent again
                    appt.reminder_sent = True
                    appt.save(update_fields=['reminder_sent'])
            except Exception as e:
                logger.error(f"Error processing reminder for appointment ID {appt.id}: {e}")
    except Exception as e:
        logger.error(f"Error in send_appointment_reminders task: {e}")

def update_missed_appointments():
    """
    Automatically marks appointments as MISSED if the end time has passed and status is APPROVED.
    """
    try:
        from booking.models import Appointment
        now = timezone.localtime()
        today = now.date()
        
        # Get all approved appointments for today or in the past
        appointments = Appointment.objects.filter(
            status='APPROVED',
            appointment_date__lte=today
        )
        
        for appt in appointments:
            try:
                naive_end = datetime.combine(appt.appointment_date, appt.end_time)
                aware_end = timezone.make_aware(naive_end)
                
                if now > aware_end:
                    appt.status = 'MISSED'
                    appt.save(update_fields=['status'])
                    logger.info(f"Appointment ID {appt.id} automatically marked as MISSED.")
            except Exception as e:
                logger.error(f"Error updating status for appointment ID {appt.id}: {e}")
    except Exception as e:
        logger.error(f"Error in update_missed_appointments task: {e}")

def start():
    """
    Initializes and starts the BackgroundScheduler.
    """
    scheduler = BackgroundScheduler()
    # Check for reminders every 30 seconds
    scheduler.add_job(
        send_appointment_reminders, 
        'interval', 
        seconds=30, 
        id='send_appointment_reminders_job', 
        replace_existing=True
    )
    # Check for missed appointments every 60 seconds
    scheduler.add_job(
        update_missed_appointments, 
        'interval', 
        minutes=1, 
        id='update_missed_appointments_job', 
        replace_existing=True
    )
    scheduler.start()
    logger.info("APScheduler started successfully for background appointment tasks.")
