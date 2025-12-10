"""
User Repository Implementation

model과 serializer_class만 지정하면 모든 CRUD가 자동으로 동작합니다.
"""
from django.db.models import Q

from apps.infrastructure.repositories.generic import GenericRepository
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


class UserRepository(GenericRepository):
    """User Repository"""
    model = User
    serializer_class = UserModelSerializer

    def get_by_email(self, email: str):
        """이메일로 사용자 조회"""
        return self.filter(Q(email=email)).first()

    def get_by_company(self, company_id: int):
        """회사 ID로 사용자 조회"""
        return self.filter(Q(company_id=company_id))

    def get_by_department(self, department_id: int):
        """부서 ID로 사용자 조회"""
        return self.filter(Q(department_id=department_id))


class DepartmentRepository(GenericRepository):
    """Department Repository"""
    model = Department
    serializer_class = DepartmentModelSerializer


class PositionRepository(GenericRepository):
    """Position Repository"""
    model = Position
    serializer_class = PositionModelSerializer

    def get_executives(self):
        """임원 직급 조회"""
        return self.filter(Q(is_executive=True))

    def get_by_hierarchy(self, min_level: int = None, max_level: int = None):
        """계층 레벨로 직급 조회"""
        queryset = self.get_queryset()
        if min_level is not None:
            queryset = queryset.filter(hierarchy_level__gte=min_level)
        if max_level is not None:
            queryset = queryset.filter(hierarchy_level__lte=max_level)
        return queryset


class UserPermissionRepository(GenericRepository):
    """UserPermission Repository"""
    model = UserPermission
    serializer_class = UserPermissionModelSerializer

    def get_by_user(self, user_id: int):
        """사용자 ID로 권한 조회"""
        return self.filter(Q(user_id=user_id))

    def get_by_phase(self, phase: str):
        """Phase로 권한 조회"""
        return self.filter(Q(phase=phase))


class PhaseAccessRuleRepository(GenericRepository):
    """PhaseAccessRule Repository"""
    model = PhaseAccessRule
    serializer_class = PhaseAccessRuleModelSerializer

    def get_by_phase(self, phase: str):
        """Phase로 접근 규칙 조회"""
        return self.filter(Q(phase=phase)).first()

class DepartmentRepository(GenericRepository):
    """Department Repository"""
    model = Department
    serializer_class = DepartmentModelSerializer

    def get_by_organization_type(self, org_type: str):
        """조직 타입으로 부서 조회"""
        return self.filter(Q(organization_type=org_type))

    def get_top_level_departments(self):
        """최상위 부서 조회"""
        return self.filter(Q(parent_department__isnull=True))

    def get_sub_departments(self, department_id: int):
        """하위 부서 조회"""
        return self.filter(Q(parent_department_id=department_id))
