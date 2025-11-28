"""
Design ViewSet

Design 도메인의 API 엔드포인트를 제공합니다.
StandardViewSetMixin을 사용하여 표준화된 응답 형식을 자동으로 사용합니다.
"""
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.decorators import action

from apps.infrastructure.repositories.designs.repository import (
    ProjectDesignRepository,
    DesignVersionRepository,
    DesignAssigneeRepository,
    DesignHistoryRepository,
)
from apps.infrastructure.responses.swagger_api_response import ApiResponse
from apps.infrastructure.views.mixins import StandardViewSetMixin
from apps.domain.designs.models import ProjectDesign, DesignVersion, DesignAssignee, DesignHistory
from apps.infrastructure.serializers.designs import (
    ProjectDesignModelSerializer,
    DesignVersionModelSerializer,
    DesignAssigneeModelSerializer,
    DesignHistoryModelSerializer,
)
from apps.infrastructure.responses.success import SuccessResponse
from apps.infrastructure.responses.error import NotFoundResponse


@extend_schema(tags=['ProjectDesign'])
class ProjectDesignViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    ProjectDesign ViewSet

    ProjectDesign 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = ProjectDesign.objects.all()
    serializer_class = ProjectDesignModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        return ProjectDesign.objects.filter(deleted_at__isnull=True)

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """설계 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """설계 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=ProjectDesignModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """설계 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=ProjectDesignModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """설계 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=ProjectDesignModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """설계 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """설계 삭제"""
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
        프로젝트별 설계 조회

        GET /api/project-designs/by-project/1/
        """
        repository = ProjectDesignRepository()
        designs = repository.get_by_project(int(project_id))
        serializer = self.get_serializer(designs, many=True)
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
        담당자별 설계 조회

        GET /api/project-designs/by-assignee/1/
        """
        repository = ProjectDesignRepository()
        designs = repository.get_by_assignee(int(user_id))
        serializer = self.get_serializer(designs, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")


@extend_schema(tags=['DesignVersion'])
class DesignVersionViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    DesignVersion ViewSet

    DesignVersion 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = DesignVersion.objects.all()
    serializer_class = DesignVersionModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        return DesignVersion.objects.filter(deleted_at__isnull=True)

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """설계 버전 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """설계 버전 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=DesignVersionModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """설계 버전 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=DesignVersionModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """설계 버전 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=DesignVersionModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """설계 버전 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """설계 버전 삭제"""
        return super().destroy(request, *args, **kwargs)

    # ========== 커스텀 액션 ==========
    @extend_schema(
        parameters=[
            OpenApiParameter("design_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-design/(?P<design_id>[^/.]+)')
    def by_design(self, request, design_id=None):
        """
        설계별 버전 조회

        GET /api/design-versions/by-design/1/
        """
        repository = DesignVersionRepository()
        versions = repository.get_by_design(int(design_id))
        serializer = self.get_serializer(versions, many=True)
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
        상태별 버전 조회

        GET /api/design-versions/by-status/APPROVED/
        """
        repository = DesignVersionRepository()
        versions = repository.get_by_status(status)
        serializer = self.get_serializer(versions, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("design_id", int, OpenApiParameter.PATH),
            OpenApiParameter("status", str, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-design-status/(?P<design_id>[^/.]+)/(?P<status>[^/.]+)')
    def by_design_status(self, request, design_id=None, status=None):
        """
        설계와 상태별 버전 조회

        GET /api/design-versions/by-design-status/1/APPROVED/
        """
        repository = DesignVersionRepository()
        versions = repository.get_by_design_and_status(int(design_id), status)
        serializer = self.get_serializer(versions, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")


@extend_schema(tags=['DesignAssignee'])
class DesignAssigneeViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    DesignAssignee ViewSet

    DesignAssignee 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = DesignAssignee.objects.all()
    serializer_class = DesignAssigneeModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        return DesignAssignee.objects.filter(deleted_at__isnull=True)

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """설계 담당자 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """설계 담당자 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=DesignAssigneeModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """설계 담당자 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=DesignAssigneeModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """설계 담당자 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=DesignAssigneeModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """설계 담당자 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """설계 담당자 삭제"""
        return super().destroy(request, *args, **kwargs)

    # ========== 커스텀 액션 ==========
    @extend_schema(
        parameters=[
            OpenApiParameter("design_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-design/(?P<design_id>[^/.]+)')
    def by_design(self, request, design_id=None):
        """
        설계별 담당자 조회

        GET /api/design-assignees/by-design/1/
        """
        repository = DesignAssigneeRepository()
        assignees = repository.get_by_design(int(design_id))
        serializer = self.get_serializer(assignees, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("design_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='primary/(?P<design_id>[^/.]+)')
    def primary(self, request, design_id=None):
        """
        설계의 주요 담당자 조회

        GET /api/design-assignees/primary/1/
        """
        repository = DesignAssigneeRepository()
        assignee = repository.get_primary_assignee(int(design_id))
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
    @action(detail=False, methods=['get'], url_path='by-user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        """
        사용자별 설계 할당 조회

        GET /api/design-assignees/by-user/1/
        """
        repository = DesignAssigneeRepository()
        assignees = repository.get_by_user(int(user_id))
        serializer = self.get_serializer(assignees, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")


@extend_schema(tags=['DesignHistory'])
class DesignHistoryViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    DesignHistory ViewSet

    DesignHistory 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = DesignHistory.objects.all()
    serializer_class = DesignHistoryModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        return DesignHistory.objects.filter(deleted_at__isnull=True)

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """설계 이력 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """설계 이력 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=DesignHistoryModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """설계 이력 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=DesignHistoryModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """설계 이력 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=DesignHistoryModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """설계 이력 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """설계 이력 삭제"""
        return super().destroy(request, *args, **kwargs)

    # ========== 커스텀 액션 ==========
    @extend_schema(
        parameters=[
            OpenApiParameter("design_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-design/(?P<design_id>[^/.]+)')
    def by_design(self, request, design_id=None):
        """
        설계별 이력 조회

        GET /api/design-histories/by-design/1/
        """
        repository = DesignHistoryRepository()
        histories = repository.get_by_design(int(design_id))
        serializer = self.get_serializer(histories, many=True)
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
        사용자별 설계 이력 조회

        GET /api/design-histories/by-user/1/
        """
        repository = DesignHistoryRepository()
        histories = repository.get_by_user(int(user_id))
        serializer = self.get_serializer(histories, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")