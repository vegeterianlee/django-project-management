# apps/presentation/api/leaves/urls.py
"""
Leaves URLs

Leaves 도메인의 URL 라우팅을 정의합니다.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.presentation.controllers.leaves.views import (
    LeaveRequestViewSet,
    LeaveGrantViewSet,
    LeaveUsageViewSet,
)

router = DefaultRouter()
router.register(r'leave-requests', LeaveRequestViewSet, basename='leave-request')
router.register(r'leave-grants', LeaveGrantViewSet, basename='leave-grant')
router.register(r'leave-usages', LeaveUsageViewSet, basename='leave-usage')

urlpatterns = [
    path('', include(router.urls)),
]