"""
Outbox Pattern Models

트랜잭션 아웃박스 패턴을 구현하여 이벤트를 안전하게 발행합니다.
소프트 삭제 이벤트를 Outbox 테이블에 저장하고, 트랜잭션 커밋 후 Celery로 전송합니다.
"""

from django.db import models
from django.utils import timezone
import json
import uuid


class OutboxEventStatus(models.TextChoices):
    """Outbox 이벤트 상태"""
    PENDING = "PENDING", "대기 중"
    PUBLISHED = "PUBLISHED", "발행됨"
    PROCESSED = "PROCESSED", "처리됨"
    FAILED = "FAILED", "실패"


class OutboxEvent(models.Model):
    """
    Outbox 이벤트 모델

    소프트 삭제 이벤트를 저장하고, 트랜잭션 커밋 후 Celery로 전송합니다.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 이벤트 타입 및 데이터
    event_type = models.CharField(
        max_length=100,
        help_text="이벤트 타입 (예: soft_delete.propagate)"
    )
    aggregate_type = models.CharField(
        max_length=100,
        help_text="집계 타입 (모델명, 예: Project)"
    )
    aggregate_id = models.CharField(
        max_length=255,
        help_text="집계 ID (모델의 PK)"
    )
    event_data = models.JSONField(
        help_text="이벤트 데이터 (JSON)"
    )

    # 상태 관리
    status = models.CharField(
        max_length=20,
        choices=OutboxEventStatus.choices,
        default=OutboxEventStatus.PENDING,
        help_text="이벤트 상태"
    )

    # 재시도 관리
    retry_count = models.IntegerField(
        default=0,
        help_text="재시도 횟수"
    )
    max_retries = models.IntegerField(
        default=3,
        help_text="최대 재시도 횟수"
    )

    # 에러 정보
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="에러 메시지"
    )
    last_error_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="마지막 에러 발생 시간"
    )
    # Celery 작업 정보
    celery_task_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Celery Task ID"
    )

    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'outbox_events'
        verbose_name = 'Outbox Event'
        verbose_name_plural = 'Outbox Events'
        ordering = ['created_at']
        indexes = [
            models.Index(
                fields=['status', 'created_at'],
                name='idx_outbox_status_created'
            ),
            models.Index(
                fields=['aggregate_type', 'aggregate_id'],
                name='idx_outbox_aggregate'
            ),
            models.Index(
                fields=['event_type'],
                name='idx_outbox_event_type'
            ),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.aggregate_type}:{self.aggregate_id} ({self.status})"

    def mark_as_published(self, celery_task_id: str = None):
        """이벤트를 발행됨으로 표시"""
        self.status = OutboxEventStatus.PUBLISHED
        self.published_at = timezone.now()
        if celery_task_id:
            self.celery_task_id = celery_task_id
        self.save(update_fields=['status', 'published_at', 'celery_task_id'])

    def mark_as_processed(self):
        """이벤트를 처리됨으로 표시"""
        self.status = OutboxEventStatus.PROCESSED
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])

    def mark_as_failed(self, error_message: str):
        """이벤트를 실패로 표시"""
        self.status = OutboxEventStatus.FAILED
        self.error_message = error_message
        self.last_error_at = timezone.now()
        self.retry_count += 1
        self.save(update_fields=['status', 'error_message', 'last_error_at', 'retry_count'])

    def should_retry(self) -> bool:
        """재시도 가능 여부 확인"""
        return self.retry_count < self.max_retries
