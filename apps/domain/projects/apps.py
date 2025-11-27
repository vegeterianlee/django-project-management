from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    """Projects 도메인 앱 설정"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.domain.projects'
    verbose_name = 'Project Management'