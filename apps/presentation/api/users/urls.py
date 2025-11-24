"""
Users URLs

Users 도메인의 URL 라우팅을 정의합니다.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.presentation.controllers.users.views import UserViewSet, DepartmentViewSet, PositionViewSet, \
    UserPermissionViewSet, PhaseAccessRuleViewSet

# DRF Router 생성
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'positions', PositionViewSet, basename='position')
router.register(r'user-permissions', UserPermissionViewSet, basename='user-permission')
router.register(r'phase-access-rules', PhaseAccessRuleViewSet, basename='phase-access-rule')

urlpatterns = [
    path('', include(router.urls)),
]