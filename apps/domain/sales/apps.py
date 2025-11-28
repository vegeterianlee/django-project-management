"""
Sales Domain AppConfig

Sales 도메인 앱 설정을 정의합니다.
"""
from django.apps import AppConfig


class SalesConfig(AppConfig):
    """Sales 도메인 앱 설정"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.domain.sales'
    verbose_name = 'Sales Management'