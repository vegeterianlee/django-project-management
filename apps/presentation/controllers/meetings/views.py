"""
Meetings ViewSet

Meetings 도메인의 API 엔드포인트를 제공합니다.
StandardViewSetMixin을 사용하여 표준화된 응답 형식을 자동으로 사용합니다.
"""
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.decorators import action

from apps.infrastructure.repositories.meetings.repository import (
    MeetingRepository,
    MeetingAssigneeRepository,
)
from apps.infrastructure.responses.swagger_api_response import ApiResponse
from apps.infrastructure.views.mixins import StandardViewSetMixin
from apps.domain.meetings.models import Meeting, MeetingAssignee
from apps.infrastructure.serializers.meetings import (
    MeetingModelSerializer,
    MeetingAssigneeModelSerializer,
)
from apps.infrastructure.responses.success import SuccessResponse


@extend_schema(tags=['Meeting'])
class MeetingViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    Meeting ViewSet

    Meeting 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = Meeting.objects.all()
    serializer_class = MeetingModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        return Meeting.objects.filter(deleted_at__isnull=True)

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """회의 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """회의 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=MeetingModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """회의 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=MeetingModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """회의 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=MeetingModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """회의 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """회의 삭제"""
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
        프로젝트별 회의 조회

        GET /api/meetings/by-project/1/
        """
        repository = MeetingRepository()
        meetings = repository.get_by_project(int(project_id))
        serializer = self.get_serializer(meetings, many=True)
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
        Phase별 회의 조회

        GET /api/meetings/by-phase/DESIGN/
        """
        repository = MeetingRepository()
        meetings = repository.get_by_phase(phase)
        serializer = self.get_serializer(meetings, many=True)
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
        프로젝트와 Phase별 회의 조회

        GET /api/meetings/by-project-phase/1/DESIGN/
        """
        repository = MeetingRepository()
        meetings = repository.get_by_project_and_phase(int(project_id), phase)
        serializer = self.get_serializer(meetings, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("creator_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-creator/(?P<creator_id>[^/.]+)')
    def by_creator(self, request, creator_id=None):
        """
        생성자별 회의 조회

        GET /api/meetings/by-creator/1/
        """
        repository = MeetingRepository()
        meetings = repository.get_by_creator(int(creator_id))
        serializer = self.get_serializer(meetings, many=True)
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
        참석자별 회의 조회

        GET /api/meetings/by-assignee/1/
        """
        repository = MeetingRepository()
        meetings = repository.get_by_assignee(int(user_id))
        serializer = self.get_serializer(meetings, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")


@extend_schema(tags=['MeetingAssignee'])
class MeetingAssigneeViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    MeetingAssignee ViewSet

    MeetingAssignee 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = MeetingAssignee.objects.all()
    serializer_class = MeetingAssigneeModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        return MeetingAssignee.objects.filter(deleted_at__isnull=True)

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """회의 참석자 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """회의 참석자 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=MeetingAssigneeModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """회의 참석자 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=MeetingAssigneeModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """회의 참석자 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=MeetingAssigneeModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """회의 참석자 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """회의 참석자 삭제"""
        return super().destroy(request, *args, **kwargs)

    # ========== 커스텀 액션 ==========
    @extend_schema(
        parameters=[
            OpenApiParameter("meeting_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-meeting/(?P<meeting_id>[^/.]+)')
    def by_meeting(self, request, meeting_id=None):
        """
        회의별 참석자 조회

        GET /api/meeting-assignees/by-meeting/1/
        """
        repository = MeetingAssigneeRepository()
        assignees = repository.get_by_meeting(int(meeting_id))
        serializer = self.get_serializer(assignees, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("user_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        """
        사용자별 회의 할당 조회

        GET /api/meeting-assignees/by-user/1/
        """
        repository = MeetingAssigneeRepository()
        assignees = repository.get_by_user(int(user_id))
        serializer = self.get_serializer(assignees, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")