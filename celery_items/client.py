import os
from datetime import timedelta

from celery import Celery
from celery.schedules import crontab

celery_app = Celery("chat_processing")
celery_app.config_from_object('celery_items.celeryconfig')
celery_app.conf.beat_schedule = {
    'events_update': {
        'task': 'google_calendar.main.get_events',
        'schedule': timedelta(seconds=30),
    },
    'events_notification': {
        'task': 'chat_processing.send_event_notification',
        'schedule': timedelta(seconds=30)
    },
    'notification_update': {
        'task': 'mongo_connect.get_events_for_notification',
        'schedule': timedelta(seconds=30)
    }
}
