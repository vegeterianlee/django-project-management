# apps/domain/approvals/models.py (새 파일)
"""
Approvals Domain Models

결재 요청 및 결재 라인 관련 도메인 모델을 정의합니다.
다양한 도메인(휴가, 구매, 지출 등)의 결재를 처리할 수 있는 일반적인 구조입니다.
"""
from django.db import models
from apps.infrastructure.time_stamp.models import TimeStampedSoftDelete
from apps.domain.users.models import User
from django.apps import apps

class ApprovalRequest(TimeStampedSoftDelete):
    """
    결재 요청 정보를 관리하는 모델입니다.

    다양한 도메인(휴가, 구매, 지출 등)의 결재를 처리할 수 있는 일반적인 구조입니다.
    """
    # 결재 요청 타입 선택지
    REQUEST_TYPE_CHOICES = [
        ('LEAVE', '휴가'),
        ('PURCHASE', '구매'),
        ('EXPENSE', '지출'),
        ('PROJECT', '프로젝트'),
    ]

    # 결재 상태 선택지
    STATUS_CHOICES = [
        ('PENDING', '대기'),
        ('IN_PROGRESS', '진행 중'),
        ('APPROVED', '승인'),
        ('REJECTED', '반려'),
        ('CANCELLED', '취소'),
    ]

    request_type = models.CharField(
        max_length=50,
        choices=REQUEST_TYPE_CHOICES,
        help_text="결재 요청 타입"
    )

    aggregate_type = models.CharField(
        max_length=100,
        help_text="집계 타입 (예: LeaveRequest)"
    )

    aggregate_id = models.BigIntegerField(
        help_text="집계 ID"
    )

    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='approval_requests',
        help_text="신청자"
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text="결재 상태"
    )

    title = models.CharField(
        max_length=255,
        help_text="결재 제목"
    )

    description = models.TextField(
        null=True,
        blank=True,
        help_text="결재 설명"
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="신청 일시"
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="승인 일시"
    )

    rejected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="반려 일시"
    )

    class Meta:
        db_table = 'approval_requests'
        verbose_name = 'Approval Request'
        verbose_name_plural = 'Approval Requests'
        indexes = [
            models.Index(fields=['requester'], name='idx_approval_request_requester'),
            models.Index(fields=['status'], name='idx_approval_request_status'),
            models.Index(fields=['request_type'], name='idx_approval_request_type'),
            models.Index(fields=['aggregate_type', 'aggregate_id'], name='idx_approval_request_aggregate'),
            models.Index(fields=['submitted_at'], name='idx_approval_request_submitted'),
        ]

    def __str__(self):
        return f"{self.get_request_type_display()} - {self.title} ({self.get_status_display()})"

    def get_aggregate_instance(self):
        """
        집계 인스턴스를 동적으로 가져옵니다.

        Returns:
            모델 인스턴스 또는 None
        """

        try:
            model = apps.get_model(self.aggregate_type)
            return model.objects.get(id=self.aggregate_id)
        except (LookupError, model.DoesNotExist):
            return None


class ApprovalLine(TimeStampedSoftDelete):
    """
    결재 라인 정보를 관리하는 모델입니다.

    결재 요청에 대한 결재 라인을 정의하며, 조직 계층에 따라 자동으로 생성됩니다.
    """
    # 결재 상태 선택지
    STATUS_CHOICES = [
        ('PENDING', '대기'),
        ('APPROVED', '승인'),
        ('REJECTED', '반려'),
    ]

    approval_request = models.ForeignKey(
        ApprovalRequest,
        on_delete=models.CASCADE,
        related_name='approval_lines',
        help_text="결재 요청"
    )

    approver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='approval_lines',
        help_text="결재자"
    )

    step_order = models.IntegerField(
        help_text="결재 순서 (낮을수록 먼저 결재)"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text="결재 상태"
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="결재 일시"
    )

    class Meta:
        db_table = 'approval_lines'
        verbose_name = 'Approval Line'
        verbose_name_plural = 'Approval Lines'
        unique_together = [['approval_request', 'step_order']]
        indexes = [
            models.Index(fields=['approval_request'], name='idx_approval_line_request'),
            models.Index(fields=['approver'], name='idx_approval_line_approver'),
            models.Index(fields=['status'], name='idx_approval_line_status'),
            models.Index(fields=['step_order'], name='idx_approval_line_order'),
        ]

    def __str__(self):
        return f"{self.approval_request.title} - Step {self.step_order}: {self.approver.name} ({self.get_status_display()})"