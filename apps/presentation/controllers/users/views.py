"""
Users ViewSet

Users 도메인의 API 엔드포인트를 제공합니다.
StandardViewSetMixin을 사용하여 표준화된 응답 형식을 자동으로 사용합니다.
"""
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.decorators import action
from django.db.models import Q

from apps.infrastructure.repositories.user.repository import UserRepository, PositionRepository, \
    UserPermissionRepository, PhaseAccessRuleRepository
from apps.infrastructure.responses.swagger_api_response import ApiResponse
from apps.infrastructure.views.mixins import StandardViewSetMixin
from apps.domain.users.models import (
    User,
    Department,
    Position,
    UserPermission,
    PhaseAccessRule,
)
from apps.infrastructure.serializers.users import (
    UserModelSerializer,
    DepartmentModelSerializer,
    PositionModelSerializer,
    UserPermissionModelSerializer,
    PhaseAccessRuleModelSerializer,
)
from apps.infrastructure.responses.success import SuccessResponse
from apps.infrastructure.responses.error import NotFoundResponse


@extend_schema(tags=['User'])
class UserViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    User ViewSet

    User 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = User.objects.all()
    serializer_class = UserModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        return User.objects.filter(deleted_at__isnull=True)

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """사용자 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """사용자 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=UserModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """사용자 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=UserModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """사용자 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=UserModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """사용자 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """사용자 삭제"""
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("email", str, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-email/(?P<email>[^/.]+)')
    def by_email(self, request, email=None):
        """
        이메일로 사용자 조회

        GET /api/users/by-email/user@example.com/
        """
        repository = UserRepository()
        user = repository.get_by_email(email)
        if user:
            serializer = self.get_serializer(user)
            return SuccessResponse(data=serializer.data, message="조회되었습니다.")
        return NotFoundResponse(message="사용자를 찾을 수 없습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("company_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-company/(?P<company_id>[^/.]+)')
    def by_company(self, request, company_id=None):
        """
        회사 ID로 사용자 목록 조회

        GET /api/users/by-company/1/
        """
        repository = UserRepository()
        users = repository.get_by_company(int(company_id))
        serializer = self.get_serializer(users, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("department_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-department/(?P<department_id>[^/.]+)')
    def by_department(self, request, department_id=None):
        """
        부서 ID로 사용자 목록 조회

        GET /api/users/by-department/1/
        """
        repository = UserRepository()
        users = repository.get_by_department(int(department_id))
        serializer = self.get_serializer(users, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")




@extend_schema(tags=['Department'])
class DepartmentViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    Department ViewSet

    Department 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentModelSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """부서 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """부서 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=DepartmentModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """부서 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=DepartmentModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """부서 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=DepartmentModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """부서 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """부서 삭제"""
        return super().destroy(request, *args, **kwargs)



@extend_schema(tags=['Position'])
class PositionViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    Position ViewSet

    Position 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = Position.objects.all()
    serializer_class = PositionModelSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """직급 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """직급 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=PositionModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """직급 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=PositionModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """직급 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=PositionModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """직급 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """직급 삭제"""
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'])
    def executives(self, request):
        """
        임원 직급 목록 조회

        GET /api/positions/executives/
        """
        repository = PositionRepository()
        positions = repository.get_executives()
        serializer = self.get_serializer(positions, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("min_level", int, OpenApiParameter.QUERY),
            OpenApiParameter("max_level", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-hierarchy')
    def by_hierarchy(self, request):
        """
        계층 레벨로 직급 조회

        GET /api/positions/by-hierarchy/?min_level=5&max_level=10
        """
        repository = PositionRepository()
        min_level = request.query_params.get('min_level', None)
        max_level = request.query_params.get('max_level', None)

        min_level = int(min_level) if min_level else None
        max_level = int(max_level) if max_level else None

        positions = repository.get_by_hierarchy(min_level, max_level)
        serializer = self.get_serializer(positions, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")



@extend_schema(tags=['UserPermission'])
class UserPermissionViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    UserPermission ViewSet

    UserPermission 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = UserPermission.objects.all()
    serializer_class = UserPermissionModelSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """사용자 권한 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """사용자 권한 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=UserPermissionModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """사용자 권한 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=UserPermissionModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """사용자 권한 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=UserPermissionModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """사용자 권한 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """사용자 권한 삭제"""
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("user_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        """
        사용자 ID로 권한 목록 조회

        GET /api/user-permissions/by-user/1/
        """
        repository = UserPermissionRepository()
        permissions = repository.get_by_user(int(user_id))
        serializer = self.get_serializer(permissions, many=True)
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
        Phase로 권한 목록 조회

        GET /api/user-permissions/by-phase/SALES/
        """
        repository = UserPermissionRepository()
        permissions = repository.get_by_phase(phase)
        serializer = self.get_serializer(permissions, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")




@extend_schema(tags=['PhaseAccessRule'])
class PhaseAccessRuleViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    PhaseAccessRule ViewSet

    PhaseAccessRule 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = PhaseAccessRule.objects.all()
    serializer_class = PhaseAccessRuleModelSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """Phase 접근 규칙 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """Phase 접근 규칙 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=PhaseAccessRuleModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """Phase 접근 규칙 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=PhaseAccessRuleModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """Phase 접근 규칙 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=PhaseAccessRuleModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """Phase 접근 규칙 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """Phase 접근 규칙 삭제"""
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("phase", str, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-phase/(?P<phase>[^/.]+)')
    def by_phase(self, request, phase=None):
        """
        Phase로 접근 규칙 조회

        GET /api/phase-access-rules/by-phase/SALES/
        """
        repository = PhaseAccessRuleRepository()
        rule = repository.get_by_phase(phase)
        if rule:
            serializer = self.get_serializer(rule)
            return SuccessResponse(data=serializer.data, message="조회되었습니다.")
        return NotFoundResponse(message="접근 규칙을 찾을 수 없습니다.")