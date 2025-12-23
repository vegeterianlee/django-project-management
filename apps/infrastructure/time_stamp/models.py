"""
Time Stamp Infrastructure Models

공통으로 사용되는 타임스탬프 및 소프트 삭제 기능을 제공하는 베이스 모델입니다.
모든 도메인 모델이 상속받아 사용할 수 있는 공통 기능을 정의합니다.
"""
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps

class TimeStampedModel(models.Model):
    """
    생성 시간과 수정 시간을 자동으로 관리하는 추상 모델입니다.

    created_at: 레코드 생성 시간 (자동 설정, 수정 불가)
    updated_at: 레코드 수정 시간 (자동 업데이트)
    """
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True  # 이 모델은 직접 인스턴스화되지 않고 상속용으로만 사용


class TimeStampedSoftDelete(TimeStampedModel):
    """
    타임스탬프와 소프트 삭제 기능을 제공하는 추상 모델입니다.

    deleted_at: 삭제 시간 (None이면 삭제되지 않음)
    is_deleted: 삭제 여부 (deleted_at이 None이 아니면 True)

    소프트 삭제: 실제로 DB에서 레코드를 삭제하지 않고 deleted_at만 설정하여
    논리적으로 삭제된 것으로 처리합니다.
    """
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """
        소프트 삭제를 수행합니다.
        실제 레코드를 삭제하지 않고 deleted_at을 현재 시간으로 설정합니다.
        """
        was_deleted = self.is_deleted

        self.deleted_at = timezone.now()
        self.save(using=using)
        if not was_deleted:
            self._create_outbox_event()

    def _create_outbox_event(self):
        from apps.infrastructure.outbox.services import OutboxService
        """
        소프트 삭제 Outbox 이벤트를 생성합니다.
        """
        model_name = self.__class__.__name__
        model_app = self._meta.app_label

        # 이벤트 데이터 구성
        event_data = {
            'model_app': model_app,
            'model_name': model_name,
            'instance_id': str(self.pk),
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
        }

        # Outbox 이벤트 생성
        OutboxService.create_outbox_event(
            aggregate_type=f"{model_app}.{model_name}",
            aggregate_id=self.pk,
            event_data=event_data,
            outbox_event_type="soft_delete.propagate"
        )


    def restore(self):
        """
        삭제된 레코드를 복원합니다.
        deleted_at을 None으로 설정하여 복원합니다.
        """
        self.deleted_at = None
        self.save()

    @property
    def is_deleted(self):
        """삭제 여부를 반환합니다."""
        return self.deleted_at is not None