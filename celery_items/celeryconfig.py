from datetime import timedelta

from celery.schedules import crontab

CELERY_IMPORTS = ('chat_processing', 'google_calendar', 'mongo_connect')
CELERY_IGNORE_RESULT = False
BROKER_HOST = '127.0.0.1'
BROKER_PORT = 6379
BROKER_URL = "redis://"
