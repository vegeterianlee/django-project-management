"""
Approvals Domain Models

결재 요청 및 결재 라인 관련 도메인 모델을 정의합니다.
"""
from django.db import models

from apps.domain.enums.departments import ORGANIZATION_TYPE_CHOICES
from apps.infrastructure.time_stamp.models import TimeStampedSoftDelete
from apps.domain.users.models import User


class ApprovalRequest(TimeStampedSoftDelete):
    """
    결재 요청 정보를 관리하는 모델입니다.

    다양한 도메인(휴가, 구매, 지출 등)의 결재를 처리할 수 있는 일반적인 구조입니다.
    LeaveRequest와 1대1 관계를 가집니다.
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
        ('PENDING', '대기 중'),
        ('IN_PROGRESS', '진행 중'),
        ('APPROVED', '승인'),
        ('REJECTED', '반려'),
        ('CANCELLED', '취소'),
    ]

    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='approval_requests',
        help_text="신청자"
    )

    request_type = models.CharField(
        max_length=50,
        choices=REQUEST_TYPE_CHOICES,
        help_text="결재 요청 타입"
    )

    # request_type_id는 LeaveRequest.id를 참조
    # LeaveRequest와 1대1 관계이므로, leave_request를 통해 접근 가능
    request_type_id = models.BigIntegerField(
        help_text="요청 타입별 ID (예: LeaveRequest.id)"
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text="결재 상태"
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

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="취소 일시"
    )

    class Meta:
        db_table = 'approval_requests'
        verbose_name = 'Approval Request'
        verbose_name_plural = 'Approval Requests'
        indexes = [
            models.Index(fields=['requester'], name='idx_approval_request_requester'),
            models.Index(fields=['status'], name='idx_approval_request_status'),
            models.Index(fields=['request_type'], name='idx_approval_request_type'),
            models.Index(fields=['submitted_at'], name='idx_approval_request_submitted'),
        ]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(status='APPROVED', approved_at__isnull=True) |
                      models.Q(status='APPROVED', approved_at__isnull=False),
                name='ck_approval_request_approved_at'
            ),
            models.CheckConstraint(
                check=~models.Q(status='REJECTED', rejected_at__isnull=True) |
                      models.Q(status='REJECTED', rejected_at__isnull=False),
                name='ck_approval_request_rejected_at'
            ),
        ]

    def __str__(self):
        return f"{self.get_request_type_display()} - {self.requester.name} ({self.get_status_display()})"

    def get_leave_request(self):
        """
        연결된 LeaveRequest를 반환합니다.

        Returns:
            LeaveRequest 또는 None
        """
        try:
            return self.leave_request
        except:
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

    step_order = models.IntegerField(
        help_text="결재 순서 (낮을수록 먼저 결재)"
    )

    approver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='approval_lines',
        help_text="결재자"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text="결재 상태"
    )

    acted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="결재 처리 일시"
    )

    comment = models.TextField(
        null=True,
        blank=True,
        help_text="결재 의견"
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
        return f"{self.approval_request} - Step {self.step_order}: {self.approver.name} ({self.get_status_display()})"


class ApprovalPolicy(TimeStampedSoftDelete):
    """
    결재 정책 정보를 관리하는 모델입니다.

    요청 타입, 부서 타입, 역할에 따라 적용되는 결재 정책을 정의합니다.
    """
    # 결재 요청 타입 선택지 (ApprovalRequest.REQUEST_TYPE_CHOICES와 동일)
    REQUEST_TYPE_CHOICES = [
        ('LEAVE', '휴가'),
        ('PURCHASE', '구매'),
        ('EXPENSE', '지출'),
        ('PROJECT', '프로젝트'),
    ]

    APPLIES_TO_ROLE = [
        ('EMPLOYEE', '팀원'),
        ('LEADER', '팀장'),
    ]

    request_type = models.CharField(
        max_length=50,
        choices=REQUEST_TYPE_CHOICES,
        help_text="결재 요청 타입"
    )

    applies_to_dept_type = models.CharField(
        max_length=50,
        choices=ORGANIZATION_TYPE_CHOICES,
        help_text="적용 대상 부서 타입"
    )

    applies_to_role = models.CharField(
        max_length=50,
        choices=APPLIES_TO_ROLE,
        help_text="적용 대상 역할"
    )

    class Meta:
        db_table = 'approval_policies'
        verbose_name = 'Approval Policy'
        verbose_name_plural = 'Approval Policies'
        indexes = [
            models.Index(fields=['request_type'], name='idx_approval_policy_type'),
            models.Index(fields=['applies_to_dept_type'], name='idx_approval_policy_dept'),
            models.Index(fields=['applies_to_role'], name='idx_approval_policy_role'),
        ]

    def __str__(self):
        dept_type = self.applies_to_dept_type
        role = self.applies_to_role
        return f"{self.get_request_type_display()} - {dept_type} - {role}"


class ApprovalPolicyStep(TimeStampedSoftDelete):
    """
    결재 정책 단계 정보를 관리하는 모델입니다.

    ApprovalPolicy에 속한 각 결재 단계를 정의합니다.
    """
    # 결재자 선택 타입 선택지
    APPROVER_SELECTOR_TYPE_CHOICES = [
        ('DEPT_MANAGER', '부서장'),
        ('PARENT_DEPT_MANAGER', '다음 부서 상사'),
        ('CEO', '대표'),
    ]

    policy = models.ForeignKey(
        ApprovalPolicy,
        on_delete=models.CASCADE,
        related_name='steps',
        help_text="결재 정책"
    )

    step_order = models.IntegerField(
        help_text="결재 단계 순서 (낮을수록 먼저 결재)"
    )

    approver_selector_type = models.CharField(
        max_length=50,
        choices=APPROVER_SELECTOR_TYPE_CHOICES,
        help_text="결재자 선택 타입"
    )

    class Meta:
        db_table = 'approval_policy_steps'
        verbose_name = 'Approval Policy Step'
        verbose_name_plural = 'Approval Policy Steps'
        unique_together = [['policy', 'step_order']]
        indexes = [
            models.Index(fields=['policy'], name='idx_approval_policy_step_policy'),
            models.Index(fields=['step_order'], name='idx_approval_policy_step_order'),
            models.Index(fields=['approver_selector_type'], name='idx_approval_policy_step_selector'),
        ]

    def __str__(self):
        return f"{self.policy} - Step {self.step_order}: {self.get_approver_selector_type_display()}"