# apps/presentation/api/approvals/urls.py
"""
Approvals URLs

Approvals 도메인의 URL 라우팅을 정의합니다.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.presentation.controllers.approvals.views import (
    ApprovalRequestViewSet,
    ApprovalLineViewSet,
    ApprovalPolicyViewSet,
    ApprovalPolicyStepViewSet,
)

router = DefaultRouter()
router.register(r'approval-requests', ApprovalRequestViewSet, basename='approval-request')
router.register(r'approval-lines', ApprovalLineViewSet, basename='approval-line')
router.register(r'approval-policies', ApprovalPolicyViewSet, basename='approval-policy')
router.register(r'approval-policy-steps', ApprovalPolicyStepViewSet, basename='approval-policy-step')

urlpatterns = [
    path('', include(router.urls)),
]