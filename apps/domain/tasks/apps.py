from django.apps import AppConfig


class TasksConfig(AppConfig):
    """Tasks 도메인 앱 설정"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.domain.tasks'
    verbose_name = 'Task Management'