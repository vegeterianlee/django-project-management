"""
Projects ViewSet

Projects 도메인의 API 엔드포인트를 제공합니다.
StandardViewSetMixin을 사용하여 표준화된 응답 형식을 자동으로 사용합니다.
"""
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.decorators import action

from apps.application.project_creation.usecase import ProjectCreationUseCase
from apps.infrastructure.repositories.projects.repository import (
    ProjectRepository,
    ProjectCompanyLinkRepository,
    ProjectAssigneeRepository, ProjectMethodRepository,
)
from apps.infrastructure.responses.swagger_api_response import ApiResponse
from apps.infrastructure.serializers.designs import ProjectDesignModelSerializer
from apps.infrastructure.serializers.sales import ProjectSalesModelSerializer
from apps.infrastructure.views.mixins import StandardViewSetMixin
from apps.domain.projects.models import Project, ProjectCompanyLink, ProjectAssignee, ProjectMethod
from apps.infrastructure.serializers.projects import (
    ProjectModelSerializer,
    ProjectCompanyLinkModelSerializer,
    ProjectAssigneeModelSerializer, ProjectMethodModelSerializer,
)
from apps.infrastructure.responses.success import SuccessResponse
from apps.infrastructure.responses.error import NotFoundResponse


@extend_schema(tags=['Project'])
class ProjectViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    Project ViewSet
    
    Project 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        return Project.objects.filter(deleted_at__isnull=True)

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """프로젝트 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """프로젝트 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=ProjectModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """프로젝트 생성"""
        # Project 검증
        project_serializer = ProjectModelSerializer(data=request.data)
        project_serializer.is_valid(raise_exception=True)

        project = project_serializer.save()
        response_serializer = self.get_serializer(project)

        return SuccessResponse(
            data=response_serializer.data,
            message='프로젝트가 생성되었습니다. 영업 및 설계 정보는 곧 생성됩니다.'
        )

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=ProjectModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """프로젝트 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=ProjectModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """프로젝트 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """프로젝트 삭제"""
        return super().destroy(request, *args, **kwargs)

    # ========== 커스텀 액션 ==========
    @extend_schema(
        parameters=[
            OpenApiParameter("status", str, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-status/(?P<status>[^/.]+)')
    def by_status(self, request, status=None):
        """
        프로젝트 상태별 조회
        
        GET /api/projects/by-status/ACTIVE/
        """
        repository = ProjectRepository()
        projects = repository.get_by_status(status)
        serializer = self.get_serializer(projects, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("project_code", str, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-code/(?P<project_code>[^/.]+)')
    def by_code(self, request, project_code=None):
        """
        프로젝트 코드로 조회
        
        GET /api/projects/by-code/PRJ001/
        """
        repository = ProjectRepository()
        project = repository.get_by_code(project_code)
        if project:
            serializer = self.get_serializer(project)
            return SuccessResponse(data=serializer.data, message="조회되었습니다.")
        return NotFoundResponse(message="프로젝트를 찾을 수 없습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("company_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-company/(?P<company_id>[^/.]+)')
    def by_company(self, request, company_id=None):
        """
        회사별 프로젝트 조회
        
        GET /api/projects/by-company/1/
        """
        repository = ProjectRepository()
        projects = repository.get_by_company(int(company_id))
        serializer = self.get_serializer(projects, many=True)
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
        담당자별 프로젝트 조회
        
        GET /api/projects/by-assignee/1/
        """
        repository = ProjectRepository()
        projects = repository.get_by_assignee(int(user_id))
        serializer = self.get_serializer(projects, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request):
        """
        진행 중인 프로젝트 조회 (현재 날짜 기준)
        
        GET /api/projects/active/
        """
        repository = ProjectRepository()
        projects = repository.get_active_projects()
        serializer = self.get_serializer(projects, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("method", str, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-method/(?P<method>[^/.]+)')
    def by_method(self, request, method=None):
        """
        공법별 프로젝트 조회

        GET /api/projects/by-method/GRB/
        """
        repository = ProjectRepository()
        projects = repository.get_by_method(method)
        serializer = self.get_serializer(projects, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")


@extend_schema(tags=['ProjectMethod'])
class ProjectMethodViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    ProjectMethod ViewSet

    ProjectMethod 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = ProjectMethod.objects.all()
    serializer_class = ProjectMethodModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        return ProjectMethod.objects.filter(deleted_at__isnull=True)

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """프로젝트-공법 연결 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """프로젝트-공법 연결 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=ProjectMethodModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """프로젝트-공법 연결 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=ProjectMethodModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """프로젝트-공법 연결 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=ProjectMethodModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """프로젝트-공법 연결 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """프로젝트-공법 연결 삭제"""
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
        프로젝트별 공법 조회

        GET /api/project-methods/by-project/1/
        """
        repository = ProjectMethodRepository()
        methods = repository.get_by_project(int(project_id))
        serializer = self.get_serializer(methods, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("method", str, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-method/(?P<method>[^/.]+)')
    def by_method(self, request, method=None):
        """
        공법별 프로젝트 조회

        GET /api/project-methods/by-method/GRB/
        """
        repository = ProjectMethodRepository()
        methods = repository.get_by_method(method)
        serializer = self.get_serializer(methods, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")



@extend_schema(tags=['ProjectCompanyLink'])
class ProjectCompanyLinkViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    ProjectCompanyLink ViewSet
    
    ProjectCompanyLink 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = ProjectCompanyLink.objects.all()
    serializer_class = ProjectCompanyLinkModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        return ProjectCompanyLink.objects.filter(deleted_at__isnull=True)

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """프로젝트-회사 연결 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """프로젝트-회사 연결 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=ProjectCompanyLinkModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """프로젝트-회사 연결 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=ProjectCompanyLinkModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """프로젝트-회사 연결 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=ProjectCompanyLinkModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """프로젝트-회사 연결 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """프로젝트-회사 연결 삭제"""
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
        프로젝트별 회사 연결 조회
        
        GET /api/project-company-links/by-project/1/
        """
        repository = ProjectCompanyLinkRepository()
        links = repository.get_by_project(int(project_id))
        serializer = self.get_serializer(links, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("role", str, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-role/(?P<role>[^/.]+)')
    def by_role(self, request, role=None):
        """
        역할별 프로젝트-회사 연결 조회
        
        GET /api/project-company-links/by-role/CLIENT/
        """
        repository = ProjectCompanyLinkRepository()
        links = repository.get_by_role(role)
        serializer = self.get_serializer(links, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("company_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-company/(?P<company_id>[^/.]+)')
    def by_company(self, request, company_id=None):
        """
        회사별 프로젝트 연결 조회
        
        GET /api/project-company-links/by-company/1/
        """
        repository = ProjectCompanyLinkRepository()
        links = repository.get_by_company(int(company_id))
        serializer = self.get_serializer(links, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")




@extend_schema(tags=['ProjectAssignee'])
class ProjectAssigneeViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    ProjectAssignee ViewSet
    
    ProjectAssignee 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = ProjectAssignee.objects.all()
    serializer_class = ProjectAssigneeModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        return ProjectAssignee.objects.filter(deleted_at__isnull=True)

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """프로젝트 담당자 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """프로젝트 담당자 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=ProjectAssigneeModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """프로젝트 담당자 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=ProjectAssigneeModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """프로젝트 담당자 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=ProjectAssigneeModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """프로젝트 담당자 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """프로젝트 담당자 삭제"""
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
        프로젝트별 담당자 조회
        
        GET /api/project-assignees/by-project/1/
        """
        repository = ProjectAssigneeRepository()
        assignees = repository.get_by_project(int(project_id))
        serializer = self.get_serializer(assignees, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("project_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='primary/(?P<project_id>[^/.]+)')
    def primary(self, request, project_id=None):
        """
        프로젝트의 주요 담당자 조회
        
        GET /api/project-assignees/primary/1/
        """
        repository = ProjectAssigneeRepository()
        assignee = repository.get_primary_assignee(int(project_id))
        if assignee:
            serializer = self.get_serializer(assignee)
            return SuccessResponse(data=serializer.data, message="조회되었습니다.")
        return NotFoundResponse(message="주요 담당자를 찾을 수 없습니다.")
