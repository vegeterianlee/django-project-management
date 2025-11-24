from django.apps import AppConfig


class CompanyConfig(AppConfig):
    """Company 도메인 앱 설정"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.domain.company'  # 전체 경로 명시
    verbose_name = 'Company Management'