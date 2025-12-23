
import os
from celery import Celery
from celery.schedules import crontab

# Django 설정 모듈 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
app = Celery('pms_v3')

# Django 설정에서 Celery 설정 로드
app.config_from_object('django.conf:settings', namespace='CELERY')

# 자동으로 tasks 모듈 발견
app.autodiscover_tasks()

# Beat Schedule
app.conf.beat_schedule = {
    # Outbox 이벤트 Fallback 발행 (15초마다)
    "outbox-fallback-publish": {
        "task": "apps.infrastructure.outbox.tasks.publish_outbox_messages",
        "schedule": 15.0,
    },

    "hourly-annual-leave_grants": {
        "task": "apps.leave.tasks.process_hourly_annual_leave_grants",
        "schedule": crontab(minute='0', hour='*/3')
    }
}

# Celery 설정
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)
