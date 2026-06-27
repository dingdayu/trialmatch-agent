# Celery tasks package
from celery import Celery

# Celery instance will be configured in main.py
celery_app = Celery("trialmatch")
