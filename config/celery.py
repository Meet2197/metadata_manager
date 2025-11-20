# config/celery.py
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

app = Celery('metadata_platform')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic tasks
app.conf.beat_schedule = {
    'sync-metadata-sources': {
        'task': 'ingestion.tasks.sync_all_sources',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
    'update-search-index': {
        'task': 'search.tasks.reindex_all',
        'schedule': crontab(hour='2', minute='0'),  # Daily at 2 AM
    },
    'cleanup-old-events': {
        'task': 'events.tasks.cleanup_old_events',
        'schedule': crontab(hour='3', minute='0'),  # Daily at 3 AM
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')