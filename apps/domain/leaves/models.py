"""
Leaves Domain Models

휴가 지급, 신청, 사용 관련 도메인 모델을 정의합니다.
"""
from django.db import models
from decimal import Decimal
from apps.infrastructure.time_stamp.models import TimeStampedSoftDelete
from apps.domain.users.models import User


class LeaveGrant(TimeStampedSoftDelete):
    """
    휴가 지급 정보를 관리하는 모델입니다.

    사용자에게 지급된 휴가를 기록하며, 남은 휴가 일수를 추적합니다.
    """
    # 지급 타입 선택지
    GRANT_TYPE_CHOICES = [
        ('ANNUAL', '연차'),
        ('MONTH', '월차'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='leave_grants',
        help_text="사용자"
    )
    grant_type = models.CharField(
        max_length=50,
        choices=GRANT_TYPE_CHOICES,
        help_text="지급 타입"
    )
    amount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="지급된 휴가 일수"
    )
    granted_at = models.DateTimeField(
        help_text="지급 일시"
    )
    remaining_amount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="남은 휴가 일수"
    )

    class Meta:
        db_table = 'leave_grants'
        verbose_name = 'Leave Grant'
        verbose_name_plural = 'Leave Grants'
        indexes = [
            models.Index(fields=['user'], name='idx_leave_grant_user'),
            models.Index(fields=['grant_type'], name='idx_leave_grant_type'),
            models.Index(fields=['granted_at'], name='idx_leave_grant_date'),
        ]

    def __str__(self):
        return f"{self.user.name} - {self.get_grant_type_display()} ({self.amount}일)"


class LeaveRequest(TimeStampedSoftDelete):
    """
    휴가 신청 정보를 관리하는 모델입니다.

    사용자가 신청한 휴가의 상세 정보와 결재 상태를 관리합니다.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='leave_requests',
        help_text="신청자"
    )

    approval_request = models.OneToOneField(
        'approvals.ApprovalRequest',
        on_delete=models.CASCADE,
        related_name='leave_request',
        null=True,
        blank=True,
        help_text="결재 요청"
    )

    start_date = models.DateField(help_text="휴가 시작일")
    end_date = models.DateField(help_text="휴가 종료일")
    total_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="총 휴가 일수"
    )
    reason = models.TextField(help_text="휴가 사유")

    # 위임 사용자 (업무 위임 대상)
    delegate_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delegated_leave_requests',
        help_text="업무 위임 사용자"
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="신청 일시"
    )

    class Meta:
        db_table = 'leave_requests'
        verbose_name = 'Leave Request'
        verbose_name_plural = 'Leave Requests'
        indexes = [
            models.Index(fields=['user'], name='idx_leave_request_user'),
            models.Index(fields=['start_date', 'end_date'], name='idx_leave_request_dates'),
            models.Index(fields=['submitted_at'], name='idx_leave_request_submitted'),
            models.Index(fields=['approval_request'], name='idx_leave_request_approval'),
        ]

    def __str__(self):
        return f"{self.user.name} - {self.start_date} ~ {self.end_date} ({self.get_phase_display()})"


class LeaveUsage(TimeStampedSoftDelete):
    """
    휴가 사용 정보를 관리하는 모델입니다.

    실제로 사용된 휴가를 기록하며, 어떤 지급분에서 차감되었는지 추적합니다.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='leave_usages',
        help_text="사용자"
    )
    grant = models.ForeignKey(
        LeaveGrant,
        on_delete=models.CASCADE,
        related_name='usages',
        help_text="휴가 지급 정보"
    )
    request = models.ForeignKey(
        LeaveRequest,
        on_delete=models.CASCADE,
        related_name='usages',
        help_text="휴가 신청 정보"
    )
    used_amount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="사용한 휴가 일수"
    )
    used_at = models.DateField(help_text="휴가 사용일")

    class Meta:
        db_table = 'leave_usages'
        verbose_name = 'Leave Usage'
        verbose_name_plural = 'Leave Usages'
        indexes = [
            models.Index(fields=['user'], name='idx_leave_usage_user'),
            models.Index(fields=['grant'], name='idx_leave_usage_grant'),
            models.Index(fields=['request'], name='idx_leave_usage_request'),
            models.Index(fields=['used_at'], name='idx_leave_usage_date'),
        ]

    def __str__(self):
        return f"{self.user.name} - {self.used_at} ({self.used_amount}일)"