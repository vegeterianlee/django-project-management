"""
Leave Approval UseCase

휴가 결재 관련 유즈케이스를 처리합니다.
"""
from typing import Optional
from django.db import transaction
from apps.domain.leaves.service import LeaveService
from apps.domain.approvals.service import ApprovalService
from apps.domain.notifications.service import NotificationService
from apps.domain.leaves.models import LeaveRequest
from apps.domain.approvals.models import ApprovalRequest, ApprovalLine
from apps.infrastructure.exceptions.exceptions import ValidationException


class LeaveApprovalUseCase:
    """
    휴가 결재 관련 유즈케이스입니다.

    책임:
    - 휴가 신청 및 결재 라인 생성
    - 결재 승인/반려 처리
    - 결재 취소 처리 (승인 완료 후 취소 포함)
    """

    @staticmethod
    @transaction.atomic
    def create_leave_request_with_approval(

    ):
        pass