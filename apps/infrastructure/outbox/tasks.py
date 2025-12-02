"""
Outbox Celery Tasks

Outbox 이벤트를 처리하고 소프트 삭제를 전파하는 Celery 작업입니다.
"""
from typing import Set, Tuple

from celery import shared_task
from django.db import transaction, models
from django.utils import timezone
from django.apps import apps
import logging

from apps.infrastructure.outbox.models import OutboxEvent, OutboxEventStatus
logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_soft_delete_propagation(self, outbox_event_id: str):
    """
    소프트 삭제 전파를 처리하는 Celery 작업

    Args:
        outbox_event_id: OutboxEvent의 UUID
    """
    try:
        # Outbox 이벤트 조회
        outbox_event = OutboxEvent.objects.get(id=outbox_event_id)

        # 이미 처리된 경우 스킵
        if outbox_event.status == OutboxEventStatus.PROCESSED:
            logger.info(f"Outbox event {outbox_event_id} already processed")
            return

        # 이벤트 데이터 추출
        event_data = outbox_event.event_data
        model_app = event_data['model_app']
        model_name = event_data['model_name']
        instance_id = event_data['instance_id']

        # 모델 가져오기
        try:
            model = apps.get_model(model_app, model_name)
        except LookupError as e:
            error_msg = f"Model {model_app}.{model_name} not found: {e}"
            logger.error(error_msg)
            outbox_event.mark_as_failed(error_msg)
            return

        # 인스턴스 가져오기
        try:
            instance = model.objects.get(pk=instance_id)
        except model.DoesNotExist:
            error_msg = f"Instance {model_name}:{instance_id} not found"
            logger.error(error_msg)
            outbox_event.mark_as_failed(error_msg)
            return

        # 소프트 삭제 전파
        with transaction.atomic():
            # 순환 참조 방지를 위한 visited 집합
            visited: Set[Tuple[str, str]] = set()

            _propagate_soft_delete_recursive(
                instance=instance,
                model=model,
                visited=visited,
                depth=0
            )

            # 이벤트를 처리됨으로 표시
            outbox_event.mark_as_processed()

        logger.info(
            f"Successfully propagated soft delete for {model_name}:{instance_id}"
        )
    except OutboxEvent.DoesNotExist:
        logger.error(f"Outbox event {outbox_event_id} not found")

    except Exception as e:
        error_msg = f"Error processing outbox event {outbox_event_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # Outbox 이벤트 업데이트
        try:
            outbox_event = OutboxEvent.objects.get(id=outbox_event_id)
            outbox_event.mark_as_failed(error_msg)

            # 재시도 가능한 경우 재시도
            if outbox_event.should_retry():
                raise self.retry(exc=e)

        except OutboxEvent.DoesNotExist:
            pass

def _propagate_soft_delete_recursive(
    instance,
    model,
    visited: Set[Tuple[str, str]],
    depth: int = 0,
    max_depth: int = 10
):
    """
    소프트 삭제를 트리 구조로 재귀적으로 전파합니다.

    Args:
        instance: 삭제된 인스턴스
        model: 인스턴스의 모델 클래스
        visited: 순환 참조 방지를 위한 방문한 인스턴스 집합
        depth: 현재 깊이 (재귀 깊이 제한용)
        max_depth: 최대 재귀 깊이 (무한 루프 방지)
    """

    # 순환 참조 방지: 이미 처리한 인스턴스는 스킵
    instance_key = (model.__name__, str(instance.pk))
    if instance_key in visited:
        logger.debug(
            f"Skipping already visited instance {model.__name__}:{instance.pk}"
        )
        return

    visited.add(instance_key)

    # 모델의 모든 FK 관계 찾기
    for field in model._meta.get_fields():
        if field.one_to_many: # 역참조만 고려
            related_model = field.related_model

            # TimeStampedSoftDelete가 있는 경우만
            if hasattr(related_model, 'deleted_at'):
                related_name = field.get_accessor_name()

                try:
                    # 하위 인스턴스들 조회 (아직 삭제되지 않은 것만)
                    related_queryset = getattr(instance, related_name).filter(
                        deleted_at__isnull=True
                    )

                    # 일괄 소프트 삭제
                    if related_queryset.exists():
                        deleted_count = related_queryset.count()

                        instance_ids = list(related_queryset.values_list('id', flat=True))

                        related_queryset.update(deleted_at=timezone.now())
                        logger.info(
                            f"[Depth {depth}] Propagated soft delete from "
                            f"{model.__name__}:{instance.pk} to "
                            f"{related_model.__name__} ({deleted_count} instances)"
                        )

                        # 저장된 ID로 다시 조회
                        updated_instances = related_model.objects.filter(
                            id__in=instance_ids
                        )

                        # 재귀적으로 각 하위 인스턴스에 대해 전파
                        for related_instance in updated_instances:
                            # 재귀 호출하여 더 깊은 레벨까지 전파
                            _propagate_soft_delete_recursive(
                                instance=related_instance,
                                model=related_model,
                                visited=visited,
                                depth=depth+1,
                                max_depth=max_depth
                            )

                except AttributeError:
                    # 역참조 필드, related_name이 없는 경우
                    logger.debug(
                        f"No related name '{related_name}' for {model.__name__}"
                    )
                    continue

                except Exception as e:
                    logger.error(
                        f"Error propagating soft delete to {related_model.__name__} "
                        f"from {model.__name__}:{instance.pk}: {e}",
                        exc_info=True
                    )

                    # 에러 발생해도 계속 진행
                    continue


@shared_task()
def publish_outbox_messages():
    """
    Fallback: 처리되지 않은 Outbox 이벤트를 재발행합니다.
    Celery Beat에 의해 주기적으로 실행됩니다.

    ⚠️ 주의: 백업용입니다. 정상적인 경우에는 사용되지 않습니다.
    """
    # PENDING 상태이지만 발행되지 않은 이벤트들
    pending_events = OutboxEvent.objects.filter(
        status=OutboxEventStatus.PENDING,
        published_at__isnull=True,
        created_at__lt=timezone.now() - timezone.timedelta(seconds=10) # 10초 이상 지난 것만
    ).order_by('created_at')[:100]

    republished_count = 0
    for event in pending_events:
        try:
            # Celery 작업 재발행
            task_result = process_soft_delete_propagation.delay(str(event.id))
            event.mark_as_published(celery_task_id=task_result.id)
            republished_count += 1
            logger.warning(f"Backup: Republished outbox event {event.id}")
        except Exception as e:
            logger.error(f"Backup: Failed to republish outbox event {event.id}: {e}")

    # FAILED 상태이지만 재시도 가능한 이벤트들
    failed_events = OutboxEvent.objects.filter(
        status=OutboxEventStatus.FAILED,
        retry_count__lt=models.F('max_retries')
    ).order_by('last_error_at')[:100]

    retried_count = 0
    for event in failed_events:
        try:
            # 재시도
            task_result = process_soft_delete_propagation.delay(str(event.id))
            event.status = OutboxEventStatus.PENDING
            event.mark_as_published(celery_task_id=task_result.id)
            retried_count += 1
            logger.info(f"Backup: Retrying failed outbox event {event.id}")
        except Exception as e:
            logger.error(f"Failed to retry outbox event {event.id}: {e}")

    if republished_count > 0 or retried_count > 0:
        logger.warning(
            f"Backup publish completed: {republished_count} republished, "
            f"{retried_count} retried"
        )

