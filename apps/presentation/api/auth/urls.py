"""
Auth URLs

인증 관련 URL 라우팅을 정의합니다.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.presentation.controllers.auth.views import AuthViewSet

# DRF Router 생성
router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')

urlpatterns = [
    path('', include(router.urls)),
]