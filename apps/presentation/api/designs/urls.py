"""
Design URLs

Design 도메인의 URL 라우팅을 정의합니다.
DRF Router를 사용하여 ViewSet을 자동으로 URL에 등록합니다.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.presentation.controllers.designs.views import (
    ProjectDesignViewSet,
    DesignVersionViewSet,
    DesignAssigneeViewSet,
    DesignHistoryViewSet,
)

# DRF Router 생성
router = DefaultRouter()

# ViewSet 등록
router.register(r'project-designs', ProjectDesignViewSet, basename='project-design')
router.register(r'design-versions', DesignVersionViewSet, basename='design-version')
router.register(r'design-assignees', DesignAssigneeViewSet, basename='design-assignee')
router.register(r'design-histories', DesignHistoryViewSet, basename='design-history')

# URL 패턴 정의
urlpatterns = [
    path('', include(router.urls)),
]