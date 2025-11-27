"""
Tasks ViewSet

Tasks 도메인의 API 엔드포인트를 제공합니다.
StandardViewSetMixin을 사용하여 표준화된 응답 형식을 자동으로 사용합니다.
"""
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.decorators import action

from apps.infrastructure.repositories.tasks.repository import (
    TaskRepository,
    TaskAssigneeRepository,
)
from apps.infrastructure.responses.swagger_api_response import ApiResponse
from apps.infrastructure.views.mixins import StandardViewSetMixin
from apps.domain.tasks.models import Task, TaskAssignee
from apps.infrastructure.serializers.tasks import (
    TaskModelSerializer,
    TaskAssigneeModelSerializer,
)
from apps.infrastructure.responses.success import SuccessResponse
from apps.infrastructure.responses.error import NotFoundResponse


@extend_schema(tags=['Task'])
class TaskViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    Task ViewSet

    Task 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = Task.objects.all()
    serializer_class = TaskModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        return Task.objects.filter(deleted_at__isnull=True)

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """작업 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """작업 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=TaskModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """작업 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=TaskModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """작업 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=TaskModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """작업 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """작업 삭제"""
        return super().destroy(request, *args, **kwargs)

    # ========== 커스텀 액션 ==========
    @extend_schema(
        parameters=[
            OpenApiParameter("project_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-project/(?P<project_id>[^/.]+)')
    def by_project(self, request, project_id=None):
        """
        프로젝트별 작업 조회

        GET /api/tasks/by-project/1/
        """
        repository = TaskRepository()
        tasks = repository.get_by_project(int(project_id))
        serializer = self.get_serializer(tasks, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("phase", str, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-phase/(?P<phase>[^/.]+)')
    def by_phase(self, request, phase=None):
        """
        Phase별 작업 조회

        GET /api/tasks/by-phase/DESIGN/
        """
        repository = TaskRepository()
        tasks = repository.get_by_phase(phase)
        serializer = self.get_serializer(tasks, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("project_id", int, OpenApiParameter.PATH),
            OpenApiParameter("phase", str, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-project-phase/(?P<project_id>[^/.]+)/(?P<phase>[^/.]+)')
    def by_project_phase(self, request, project_id=None, phase=None):
        """
        프로젝트와 Phase별 작업 조회

        GET /api/tasks/by-project-phase/1/DESIGN/
        """
        repository = TaskRepository()
        tasks = repository.get_by_project_and_phase(int(project_id), phase)
        serializer = self.get_serializer(tasks, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("status", str, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-status/(?P<status>[^/.]+)')
    def by_status(self, request, status=None):
        """
        상태별 작업 조회

        GET /api/tasks/by-status/DOING/
        """
        repository = TaskRepository()
        tasks = repository.get_by_status(status)
        serializer = self.get_serializer(tasks, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("priority", str, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-priority/(?P<priority>[^/.]+)')
    def by_priority(self, request, priority=None):
        """
        우선순위별 작업 조회

        GET /api/tasks/by-priority/HIGH/
        """
        repository = TaskRepository()
        tasks = repository.get_by_priority(priority)
        serializer = self.get_serializer(tasks, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("user_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-assignee/(?P<user_id>[^/.]+)')
    def by_assignee(self, request, user_id=None):
        """
        담당자별 작업 조회

        GET /api/tasks/by-assignee/1/
        """
        repository = TaskRepository()
        tasks = repository.get_by_assignee(int(user_id))
        serializer = self.get_serializer(tasks, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request):
        """
        진행 중인 작업 조회 (현재 날짜 기준)

        GET /api/tasks/active/
        """
        repository = TaskRepository()
        tasks = repository.get_active_tasks()
        serializer = self.get_serializer(tasks, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")


@extend_schema(tags=['TaskAssignee'])
class TaskAssigneeViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    TaskAssignee ViewSet

    TaskAssignee 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = TaskAssignee.objects.all()
    serializer_class = TaskAssigneeModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        return TaskAssignee.objects.filter(deleted_at__isnull=True)

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """작업 담당자 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """작업 담당자 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=TaskAssigneeModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """작업 담당자 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=TaskAssigneeModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """작업 담당자 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=TaskAssigneeModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """작업 담당자 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """작업 담당자 삭제"""
        return super().destroy(request, *args, **kwargs)

    # ========== 커스텀 액션 ==========
    @extend_schema(
        parameters=[
            OpenApiParameter("task_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-task/(?P<task_id>[^/.]+)')
    def by_task(self, request, task_id=None):
        """
        작업별 담당자 조회

        GET /api/task-assignees/by-task/1/
        """
        repository = TaskAssigneeRepository()
        assignees = repository.get_by_task(int(task_id))
        serializer = self.get_serializer(assignees, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("task_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='primary/(?P<task_id>[^/.]+)')
    def primary(self, request, task_id=None):
        """
        작업의 주요 담당자 조회

        GET /api/task-assignees/primary/1/
        """
        repository = TaskAssigneeRepository()
        assignee = repository.get_primary_assignee(int(task_id))
        if assignee:
            serializer = self.get_serializer(assignee)
            return SuccessResponse(data=serializer.data, message="조회되었습니다.")
        return NotFoundResponse(message="주요 담당자를 찾을 수 없습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("user_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-users/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        """
        사용자별 작업 할당 조회

        GET /api/task-assignees/by-users/1/
        """
        repository = TaskAssigneeRepository()
        assignees = repository.get_by_user(int(user_id))
        serializer = self.get_serializer(assignees, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")