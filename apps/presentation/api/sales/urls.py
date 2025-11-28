"""
Sales URLs

Sales 도메인의 URL 라우팅을 정의합니다.
DRF Router를 사용하여 ViewSet을 자동으로 URL에 등록합니다.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.presentation.controllers.sales.views import (
    ProjectSalesViewSet,
    SalesAssigneeViewSet,
    SalesHistoryViewSet,
)

# DRF Router 생성
router = DefaultRouter()

# ViewSet 등록
router.register(r'project-sales', ProjectSalesViewSet, basename='project-sales')
router.register(r'sales-assignees', SalesAssigneeViewSet, basename='sales-assignee')
router.register(r'sales-histories', SalesHistoryViewSet, basename='sales-history')

# URL 패턴 정의
urlpatterns = [
    path('', include(router.urls)),
]