from django.utils import timezone
from .models import Appointment
from datetime import datetime
from django.core.management.base import BaseCommand
from background_task import background
from background_task.management.commands.process_tasks import Command as ProcessTasksCommand



@background(schedule=1) 
def update_appointments_status():
        now = timezone.now()
        appointments = Appointment.objects.filter(status='not_complete', date__isnull=False, end_time__isnull=False)

        for appointment in appointments:

            end_datetime = timezone.make_aware(datetime.combine(appointment.date, appointment.end_time))
            
            if end_datetime < now:
                appointment.status = 'complete'
                appointment.save()







