from django.apps import AppConfig


class ApprovalsConfig(AppConfig):
    """Approvals 도메인 앱 설정"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.domain.approvals'  # 전체 경로 명시
    verbose_name = 'Approvals Management'