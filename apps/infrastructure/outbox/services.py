"""
Outbox Services

Outbox 이벤트 생성 및 발행을 담당하는 서비스입니다.
"""
from django.db import transaction, models
from django.utils import timezone
from typing import Dict, Any, Optional
import uuid

from apps.infrastructure.outbox.models import OutboxEvent, OutboxEventStatus
from apps.infrastructure.outbox.tasks import process_soft_delete_propagation


def _publish_event_immediately(event: OutboxEvent):
    """
    Outbox 이벤트를 즉시 Celery로 발행합니다.
    트랜잭션 커밋 후 호출됩니다.

    Args:
        event: 발행할 Outbox 이벤트
    """

    # Celery 작업 실행
    try:
        task_result = process_soft_delete_propagation.delay(str(event.id))
        # 이벤트를 발행됨으로 표시
        event.mark_as_published(celery_task_id=task_result.id)

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(
            f"Failed to publish outbox event {event.id} immediately: {e}",
            exc_info=True
        )


class OutboxService:
    """Outbox 이벤트 관리 서비스"""

    @staticmethod
    def create_soft_delete_event(
        aggregate_type: str,
        aggregate_id: str,
        event_data: Dict[str, Any]
    ) -> OutboxEvent:
        """
        소프트 삭제 이벤트를 생성합니다.
        트랜잭션 커밋 후 즉시 Celery로 전송됩니다.

        Args:
            aggregate_type: 집계 타입 (모델명)
            aggregate_id: 집계 ID (PK)
            event_data: 이벤트 데이터

        Returns:
            OutboxEvent: 생성된 Outbox 이벤트
        """
        event = OutboxEvent.objects.create(
            id=uuid.uuid4(),
            event_type="soft_delete.propagate",
            aggregate_type=aggregate_type,
            aggregate_id=str(aggregate_id),
            event_data=event_data,
            status=OutboxEventStatus.PENDING,
        )

        # 트랜잭션 커밋 후 Celery 작업 발행
        transaction.on_commit(
            lambda: _publish_event_immediately(event)
        )

        return event

    # @staticmethod
    # def mark_as_published(event: OutboxEvent, celery_task_id: str = None):
    #     """이벤트를 발행됨으로 표시"""
    #     event.status = OutboxEventStatus.PUBLISHED
    #     event.published_at = timezone.now()
    #     if celery_task_id:
    #         event.celery_task_id = celery_task_id
    #     event.save(update_fields=['status', 'published_at', 'celery_task_id'])
    #
    # @staticmethod
    # def mark_as_processed(event: OutboxEvent):
    #     """이벤트를 처리됨으로 표시"""
    #     event.status = OutboxEventStatus.PROCESSED
    #     event.processed_at = timezone.now()
    #     event.save(update_fields=['status', 'processed_at'])

    @staticmethod
    def get_pending_events(limit: int = 100):
        """처리 대기 중인 이벤트 조회"""
        return OutboxEvent.objects.filter(
            status=OutboxEventStatus.PENDING
        ).order_by('created_at')[:limit]

    @staticmethod
    def get_failed_events_for_retry(limit: int = 100):
        """재시도 가능한 실패 이벤트 조회"""
        return OutboxEvent.objects.filter(
            status=OutboxEventStatus.FAILED,
            retry_count__lt=models.F('max_retries')
        ).order_by('last_error_at')[:limit]
