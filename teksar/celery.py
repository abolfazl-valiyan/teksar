import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'teksar.settings')

app = Celery('teksar')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
