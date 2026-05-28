from django.apps import AppConfig
import sys
import os

class BookingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'booking'

    def ready(self):
        # Start the scheduler
        if 'runserver' in sys.argv:
            if os.environ.get('RUN_MAIN') == 'true':
                from . import scheduler
                scheduler.start()
        else:
            ignored_commands = ['migrate', 'makemigrations', 'collectstatic', 'shell', 'test', 'createsuperuser']
            if not any(cmd in sys.argv for cmd in ignored_commands):
                from . import scheduler
                scheduler.start()
