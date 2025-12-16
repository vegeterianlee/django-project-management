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

    total_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="지급된 휴가 일수"
    )

    remaining_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="남은 휴가 일수"
    )

    granted_at = models.DateTimeField(
        help_text="지급 일시"
    )

    expires_at = models.DateField(
        null=True,
        blank=True,
        help_text="만료일 (None이면 만료 없음)"
    )

    class Meta:
        db_table = 'leave_grants'
        verbose_name = 'Leave Grant'
        verbose_name_plural = 'Leave Grants'
        indexes = [
            models.Index(fields=['user'], name='idx_leave_grant_user'),
            models.Index(fields=['grant_type'], name='idx_leave_grant_type'),
            models.Index(fields=['granted_at'], name='idx_leave_grant_date'),
            models.Index(fields=['expires_at'], name='idx_leave_grant_expires'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(remaining_days__gte=0),
                name='ck_leave_grant_remaining_non_negative'
            ),
            models.CheckConstraint(
                check=models.Q(remaining_days__lte=models.F('total_days')),
                name='ck_leave_grant_remaining_lte_total'
            ),
        ]

    def __str__(self):
        return f"{self.user.name} - {self.get_grant_type_display()} ({self.total_days}일)"


class LeaveRequest(TimeStampedSoftDelete):
    """
    휴가 신청 정보를 관리하는 모델입니다.

    사용자가 신청한 휴가의 상세 정보와 상태를 관리합니다.
    ApprovalRequest와 1대1 관계를 가집니다.
    """
    # 휴가 타입 선택지
    LEAVE_TYPE_CHOICES = [
        ('ANNUAL', '연차'),
        ('HALF_MORNING', '오전반차'),
        ('HALF_AFTERNOON', '오후반차'),
        ('SICK_LEAVE', '병가'),
        ('LEAVE_OF_ABSENCE', '휴직'),
        ('EARLY_LEAVE', '조퇴'),
    ]

    # 휴가 신청 상태 선택지
    STATUS_CHOICES = [
        ('PENDING', '대기 중'),
        ('APPROVED', '승인'),
        ('REJECTED', '반려'),
        ('CANCELLED', '취소'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='leave_requests',
        help_text="신청자"
    )

    # 1대1 관계: ApprovalRequest와 연결
    approval_request = models.OneToOneField(
        'approvals.ApprovalRequest',
        on_delete=models.CASCADE,
        related_name='leave_request',
        help_text="결재 요청 (1대1 관계)"
    )

    leave_type = models.CharField(
        max_length=50,
        choices=LEAVE_TYPE_CHOICES,
        help_text="휴가 타입"
    )

    start_date = models.DateField(
        help_text="휴가 시작일"
    )

    end_date = models.DateField(
        help_text="휴가 종료일"
    )

    total_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="총 휴가 일수"
    )

    reason = models.TextField(
        help_text="휴가 사유"
    )

    # 위임 사용자 (업무 위임 대상)
    delegate_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='delegated_leave_requests',
        help_text="업무 위임 사용자"
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text="휴가 신청 상태"
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="신청 일시"
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="취소 일시"
    )

    cancel_reason = models.TextField(
        null=True,
        blank=True,
        help_text="취소 사유"
    )

    class Meta:
        db_table = 'leave_requests'
        verbose_name = 'Leave Request'
        verbose_name_plural = 'Leave Requests'
        indexes = [
            models.Index(fields=['user'], name='idx_leave_request_user'),
            models.Index(fields=['start_date', 'end_date'], name='idx_leave_request_dates'),
            models.Index(fields=['submitted_at'], name='idx_leave_request_submitted'),
            models.Index(fields=['status'], name='idx_leave_request_status'),
            models.Index(fields=['leave_type'], name='idx_leave_request_type'),
            models.Index(fields=['approval_request'], name='idx_leave_request_approval'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(start_date__lte=models.F('end_date')),
                name='ck_leave_request_date_order'
            ),
            models.CheckConstraint(
                check=models.Q(total_days__gt=0),
                name='ck_leave_request_total_days_positive'
            ),
        ]

    def __str__(self):
        approval_status = self.approval_request.get_status_display() if self.approval_request else "미결재"
        return f"{self.user.name} - {self.start_date} ~ {self.end_date} ({approval_status})"


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

    leave_grant = models.ForeignKey(
        LeaveGrant,
        on_delete=models.CASCADE,
        related_name='usages',
        help_text="휴가 지급 정보"
    )

    leave_request = models.ForeignKey(
        LeaveRequest,
        on_delete=models.CASCADE,
        related_name='usages',
        help_text="휴가 신청 정보"
    )

    used_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="사용한 휴가 일수"
    )

    used_date = models.DateField(
        help_text="휴가 사용일"
    )

    class Meta:
        db_table = 'leave_usages'
        verbose_name = 'Leave Usage'
        verbose_name_plural = 'Leave Usages'
        indexes = [
            models.Index(fields=['user'], name='idx_leave_usage_user'),
            models.Index(fields=['leave_grant'], name='idx_leave_usage_grant'),
            models.Index(fields=['leave_request'], name='idx_leave_usage_request'),
            models.Index(fields=['used_date'], name='idx_leave_usage_date'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(used_days__gt=0),
                name='ck_leave_usage_days_positive'
            ),
        ]

    def __str__(self):
        return f"{self.user.name} - {self.used_date} ({self.used_days}일)"