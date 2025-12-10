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
from django.utils import timezone
from datetime import timedelta


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
        default='IN_PROGRESS',
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


class ApprovalReference(TimeStampedSoftDelete):
    """
    결재 참조자(참관자) 정보를 관리하는 모델입니다.

    결재 라인과 별도로 참조자 목록을 관리합니다.
    참조자는 결재 진행 상황을 알림으로 받지만, 결재 권한은 없습니다.
    """

    approval_request = models.ForeignKey(
        ApprovalRequest,
        on_delete=models.CASCADE,
        related_name='references',
        help_text="결재 요청"
    )

    referencer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='referenced_approvals',
        help_text="참조자"
    )

    is_notified = models.BooleanField(
        default=False,
        help_text="알림 받았는지 여부"
    )

    class Meta:
        db_table = 'approval_references'
        verbose_name = 'Approval Reference'
        verbose_name_plural = 'Approval References'
        unique_together = [['approval_request','referencer']]
        indexes = [
            models.Index(fields=['approval_request'], name='idx_approval_reference_request'),
            models.Index(fields=['referencer'], name='idx_approval_referencer'),
        ]

    def __str__(self):
        return f"{self.approval_request.title} - 참조: {self.referencer.name}"



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

    comment = models.TextField(
        null=True,
        blank=True,
        help_text="결재 의견"
    )

    is_ceo_approval = models.BooleanField(
        default=False,
        help_text="대표 결재 여부 (경영 지원팀 알림 발송용)"
    )

    delay_notification_sent = models.BooleanField(
        default=False,
        help_text="지연 알림 발송 여부 (3일 이상 지연 시 경영 관리팀 알림)"
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
            models.Index(fields=['is_ceo_approval'], name='idx_approval_line_ceo'),
            models.Index(fields=['status', 'created_at'], name='idx_approval_line_status_created'),
        ]

    def __str__(self):
        return f"{self.approval_request.title} - Step {self.step_order}: {self.approver.name} ({self.get_status_display()})"

    def is_delayed(self, days: int = 3) -> bool:
        """
        결재가 지연되었는지 확인합니다.

        Args:
            days: 지연 기준 일수 (기본 3일)

        Returns:
            bool: 지연 여부
        """
        delay_threshold = timezone.now() - timedelta(days=days)
        return self.created_at < delay_threshold