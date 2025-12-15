"""
Leaves Domain AppConfig

Leaves 도메인 앱 설정을 정의합니다.
"""
from django.apps import AppConfig


class LeaveConfig(AppConfig):
    """Design 도메인 앱 설정"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.domain.leaves'
    verbose_name = 'Leaves Management'