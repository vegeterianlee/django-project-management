"""
Tasks URLs

Tasks 도메인의 URL 라우팅을 정의합니다.
DRF Router를 사용하여 ViewSet을 자동으로 URL에 등록합니다.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.presentation.controllers.tasks.views import (
    TaskViewSet,
    TaskAssigneeViewSet,
)

# DRF Router 생성
router = DefaultRouter()

# ViewSet 등록
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'task-assignees', TaskAssigneeViewSet, basename='task-assignee')

# URL 패턴 정의
urlpatterns = [
    path('', include(router.urls)),
]