"""
Notifications Domain Models

알림 관련 도메인 모델을 정의합니다.
"""
from django.db import models
from apps.infrastructure.time_stamp.models import TimeStampedSoftDelete
from apps.domain.users.models import User
from django.utils import timezone

class Notification(TimeStampedSoftDelete):
    """
    알림 정보를 관리하는 모델입니다.

    사용자 간 알림 및 시스템 이벤트 알림을 관리합니다.
    """
    # 알림 상태 선택지
    STATUS_CHOICES = [
        ('UNREAD', '읽지 않음'),
        ('READ', '읽음'),
    ]

    # 이벤트 타입 선택지
    EVENT_TYPE_CHOICES = [
        ('LEAVE_REQUEST', '휴가 신청'),
        ('LEAVE_APPROVED', '휴가 승인'),
        ('LEAVE_REJECTED', '휴가 반려'),

        ('APPROVAL_REQUIRED', '결재 요청'),
        ('APPROVAL_APPROVED', '결재 승인'),
        ('APPROVAL_REJECTED', '결재 반려'),

        ('PROJECT_ASSIGNED', '프로젝트 할당'),
        ('TASK_ASSIGNED', '작업 할당'),
    ]

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_notifications',
        help_text="발신자"
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_notifications',
        help_text="수신자"
    )
    aggregate_type = models.CharField(
        max_length=100,
        help_text="집계 타입 (예: LeaveRequest, ApprovalLine)"
    )
    aggregate_id = models.BigIntegerField(
        help_text="집계 ID"
    )
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPE_CHOICES,
        help_text="이벤트 타입"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='UNREAD',
        help_text="알림 상태"
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="알림 설명"
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="읽은 일시"
    )

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['receiver'], name='idx_notification_receiver'),
            models.Index(fields=['status'], name='idx_notification_status'),
            models.Index(fields=['aggregate_type', 'aggregate_id'], name='idx_notification_aggregate'),
            models.Index(fields=['created_at'], name='idx_notification_created'),
        ]

    def __str__(self):
        return f"{self.sender.name} → {self.receiver.name}: {self.get_event_type_display()}"

    def mark_as_read(self):
        """알림을 읽음으로 표시합니다."""
        if self.status == 'UNREAD':
            self.status = 'READ'
            self.read_at = timezone.now()
            self.save()