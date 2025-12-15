"""
Approval Domain AppConfig

Approval 도메인 앱 설정을 정의합니다.
"""
from django.apps import AppConfig


class ApprovalConfig(AppConfig):
    """Approval 도메인 앱 설정"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.domain.approvals'
    verbose_name = 'Approvals Management'