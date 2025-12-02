"""
Outbox AppConfig

Outbox 인프라스트럭처 앱 설정입니다.
"""
from django.apps import AppConfig


class OutboxConfig(AppConfig):
    """Outbox 앱 설정"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.infrastructure.outbox'
    verbose_name = 'Outbox Infrastructure'