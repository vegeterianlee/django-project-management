"""
Meetings URLs

Meetings 도메인의 URL 라우팅을 정의합니다.
DRF Router를 사용하여 ViewSet을 자동으로 URL에 등록합니다.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.presentation.controllers.meetings.views import (
    MeetingViewSet,
    MeetingAssigneeViewSet,
)

# DRF Router 생성
router = DefaultRouter()

# ViewSet 등록
router.register(r'meetings', MeetingViewSet, basename='meeting')
router.register(r'meeting-assignees', MeetingAssigneeViewSet, basename='meeting-assignee')

# URL 패턴 정의
urlpatterns = [
    path('', include(router.urls)),
]