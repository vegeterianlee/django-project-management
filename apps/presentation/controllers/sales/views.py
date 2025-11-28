"""
Sales ViewSet

Sales 도메인의 API 엔드포인트를 제공합니다.
StandardViewSetMixin을 사용하여 표준화된 응답 형식을 자동으로 사용합니다.
"""
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.decorators import action

from apps.infrastructure.repositories.sales.repository import (
    ProjectSalesRepository,
    SalesAssigneeRepository,
    SalesHistoryRepository,
)
from apps.infrastructure.responses.swagger_api_response import ApiResponse
from apps.infrastructure.views.mixins import StandardViewSetMixin
from apps.domain.sales.models import ProjectSales, SalesAssignee, SalesHistory
from apps.infrastructure.serializers.sales import (
    ProjectSalesModelSerializer,
    SalesAssigneeModelSerializer,
    SalesHistoryModelSerializer,
)
from apps.infrastructure.responses.success import SuccessResponse
from apps.infrastructure.responses.error import NotFoundResponse


@extend_schema(tags=['ProjectSales'])
class ProjectSalesViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    ProjectSales ViewSet

    ProjectSales 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = ProjectSales.objects.all()
    serializer_class = ProjectSalesModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        return ProjectSales.objects.filter(deleted_at__isnull=True)

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """영업 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """영업 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=ProjectSalesModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """영업 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=ProjectSalesModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """영업 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=ProjectSalesModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """영업 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """영업 삭제"""
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
        프로젝트별 영업 조회

        GET /api/project-sales/by-project/1/
        """
        repository = ProjectSalesRepository()
        sales = repository.get_by_project(int(project_id))
        serializer = self.get_serializer(sales, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("sales_type", str, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-type/(?P<sales_type>[^/.]+)')
    def by_type(self, request, sales_type=None):
        """
        영업 유형별 조회

        GET /api/project-sales/by-type/METHOD_REVIEW/
        """
        repository = ProjectSalesRepository()
        sales = repository.get_by_sales_type(sales_type)
        serializer = self.get_serializer(sales, many=True)
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
        담당자별 영업 조회

        GET /api/project-sales/by-assignee/1/
        """
        repository = ProjectSalesRepository()
        sales = repository.get_by_assignee(int(user_id))
        serializer = self.get_serializer(sales, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")


@extend_schema(tags=['SalesAssignee'])
class SalesAssigneeViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    SalesAssignee ViewSet

    SalesAssignee 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = SalesAssignee.objects.all()
    serializer_class = SalesAssigneeModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        return SalesAssignee.objects.filter(deleted_at__isnull=True)

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """영업 담당자 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """영업 담당자 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=SalesAssigneeModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """영업 담당자 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=SalesAssigneeModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """영업 담당자 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=SalesAssigneeModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """영업 담당자 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """영업 담당자 삭제"""
        return super().destroy(request, *args, **kwargs)

    # ========== 커스텀 액션 ==========
    @extend_schema(
        parameters=[
            OpenApiParameter("sales_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-sales/(?P<sales_id>[^/.]+)')
    def by_sales(self, request, sales_id=None):
        """
        영업별 담당자 조회

        GET /api/sales-assignees/by-sales/1/
        """
        repository = SalesAssigneeRepository()
        assignees = repository.get_by_sales(int(sales_id))
        serializer = self.get_serializer(assignees, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("sales_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='primary/(?P<sales_id>[^/.]+)')
    def primary(self, request, sales_id=None):
        """
        영업의 주요 담당자 조회

        GET /api/sales-assignees/primary/1/
        """
        repository = SalesAssigneeRepository()
        assignee = repository.get_primary_assignee(int(sales_id))
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
        사용자별 영업 할당 조회

        GET /api/sales-assignees/by-user/1/
        """
        repository = SalesAssigneeRepository()
        assignees = repository.get_by_user(int(user_id))
        serializer = self.get_serializer(assignees, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")


@extend_schema(tags=['SalesHistory'])
class SalesHistoryViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    SalesHistory ViewSet

    SalesHistory 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = SalesHistory.objects.all()
    serializer_class = SalesHistoryModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        return SalesHistory.objects.filter(deleted_at__isnull=True)

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """영업 이력 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """영업 이력 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=SalesHistoryModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """영업 이력 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=SalesHistoryModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """영업 이력 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=SalesHistoryModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """영업 이력 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """영업 이력 삭제"""
        return super().destroy(request, *args, **kwargs)

    # ========== 커스텀 액션 ==========
    @extend_schema(
        parameters=[
            OpenApiParameter("sales_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-sales/(?P<sales_id>[^/.]+)')
    def by_sales(self, request, sales_id=None):
        """
        영업별 이력 조회

        GET /api/sales-histories/by-sales/1/
        """
        repository = SalesHistoryRepository()
        histories = repository.get_by_sales(int(sales_id))
        serializer = self.get_serializer(histories, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("sales_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='public/(?P<sales_id>[^/.]+)')
    def public(self, request, sales_id=None):
        """
        영업의 공개 이력 조회

        GET /api/sales-histories/public/1/
        """
        repository = SalesHistoryRepository()
        histories = repository.get_public_histories(int(sales_id))
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
        사용자별 영업 이력 조회

        GET /api/sales-histories/by-user/1/
        """
        repository = SalesHistoryRepository()
        histories = repository.get_by_user(int(user_id))
        serializer = self.get_serializer(histories, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")