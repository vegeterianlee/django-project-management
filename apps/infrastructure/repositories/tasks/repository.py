"""
Task Repository Implementation

model과 serializer_class만 지정하면 모든 CRUD가 자동으로 동작합니다.
복잡한 쿼리는 커스텀 메서드로 구현합니다.
"""
from django.db.models import Q
from django.utils import timezone
from datetime import datetime

from apps.infrastructure.repositories.generic import GenericRepository
from apps.domain.tasks.models import Task, TaskAssignee
from apps.infrastructure.serializers.tasks import (
    TaskModelSerializer,
    TaskAssigneeModelSerializer,
)


class TaskRepository(GenericRepository):
    """
    Task Repository

    model과 serializer_class만 지정하면 GenericRepository의 모든 기능을 사용할 수 있습니다.
    """
    model = Task
    serializer_class = TaskModelSerializer

    def get_by_project(self, project_id: int):
        """
        프로젝트별 작업 조회

        Args:
            project_id: 프로젝트 ID

        Returns:
            QuerySet
        """
        return self.filter(Q(project_id=project_id))

    def get_by_phase(self, phase: str):
        """
        Phase별 작업 조회

        Args:
            phase: 프로젝트 Phase

        Returns:
            QuerySet
        """
        return self.filter(Q(phase=phase))

    def get_by_project_and_phase(self, project_id: int, phase: str):
        """
        프로젝트와 Phase별 작업 조회

        Args:
            project_id: 프로젝트 ID
            phase: 프로젝트 Phase

        Returns:
            QuerySet
        """
        return self.filter(Q(project_id=project_id, phase=phase))

    def get_by_status(self, status: str):
        """
        상태별 작업 조회

        Args:
            status: 작업 상태

        Returns:
            QuerySet
        """
        return self.filter(Q(status=status))

    def get_by_priority(self, priority: str):
        """
        우선순위별 작업 조회

        Args:
            priority: 작업 우선순위

        Returns:
            QuerySet
        """
        return self.filter(Q(priority=priority))

    def get_by_assignee(self, user_id: int):
        """
        담당자별 작업 조회 (TaskAssignee를 통한)

        Args:
            user_id: 사용자 ID

        Returns:
            QuerySet
        """
        # TaskAssignee를 통해 연결된 작업 조회
        task_ids = TaskAssignee.objects.filter(
            user_id=user_id,
            deleted_at__isnull=True
        ).values_list('task_id', flat=True)

        return self.filter(Q(id__in=task_ids))

    def get_active_tasks(self):
        """
        진행 중인 작업 조회 (현재 날짜 기준)

        Returns:
            QuerySet
        """
        now = timezone.now()
        return self.filter(
            Q(start_date__lte=now) & Q(end_date__gte=now) & Q(status="DOING")
        )


class TaskAssigneeRepository(GenericRepository):
    """
    TaskAssignee Repository
    """
    model = TaskAssignee
    serializer_class = TaskAssigneeModelSerializer

    def get_by_task(self, task_id: int):
        """작업별 담당자 조회"""
        return self.filter(Q(task_id=task_id))

    def get_primary_assignee(self, task_id: int):
        """작업의 주요 담당자 조회"""
        return self.filter(Q(task_id=task_id, is_primary=True)).first()

    def get_by_user(self, user_id: int):
        """사용자별 작업 할당 조회"""
        return self.filter(Q(user_id=user_id))