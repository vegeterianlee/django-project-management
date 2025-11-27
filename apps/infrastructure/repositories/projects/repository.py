# apps/infrastructure/repositories/project/repository.py
"""
Project Repository Implementation

model과 serializer_class만 지정하면 모든 CRUD가 자동으로 동작합니다.
복잡한 쿼리는 커스텀 메서드로 Repository 구현했습니다.
"""
from django.db.models import Q
from django.utils import timezone
from datetime import date

from apps.infrastructure.repositories.generic import GenericRepository
from apps.domain.projects.models import Project, ProjectCompanyLink, ProjectAssignee
from apps.infrastructure.serializers.projects import (
    ProjectModelSerializer,
    ProjectCompanyLinkModelSerializer,
    ProjectAssigneeModelSerializer,
)


class ProjectRepository(GenericRepository):
    """
    Project Repository

    model과 serializer_class만 지정하면 GenericRepository의 모든 기능을 사용할 수 있습니다.
    """
    model = Project
    serializer_class = ProjectModelSerializer

    def get_by_status(self, status: str):
        """
        프로젝트 상태별 조회

        Args:
            status: 프로젝트 상태

        Returns:
            QuerySet
        """
        return self.filter(Q(status=status))

    def get_by_code(self, project_code: str):
        """
        프로젝트 코드로 조회

        Args:
            project_code: 프로젝트 코드

        Returns:
            Project 인스턴스 또는 None
        """
        return self.filter(Q(project_code=project_code)).first()

    def get_by_company(self, company_id: int):
        """
        회사별 프로젝트 조회 (ProjectCompanyLink를 통한)

        Args:
            company_id: 회사 ID

        Returns:
            QuerySet
        """
        # ProjectCompanyLink를 통해 연결된 프로젝트 조회
        project_ids = ProjectCompanyLink.objects.filter(
            company_id=company_id,
            deleted_at__isnull=True
        ).values_list('project_id', flat=True)

        return self.filter(Q(id__in=project_ids))

    def get_by_assignee(self, user_id: int):
        """
        담당자별 프로젝트 조회 (ProjectAssignee를 통한)

        Args:
            user_id: 사용자 ID

        Returns:
            QuerySet
        """
        # ProjectAssignee를 통해 연결된 프로젝트 조회
        project_ids = ProjectAssignee.objects.filter(
            user_id=user_id,
            deleted_at__isnull=True
        ).values_list('project_id', flat=True)

        return self.filter(Q(id__in=project_ids))

    def get_active_projects(self):
        """
        진행 중인 프로젝트 조회 (현재 날짜 기준)

        Returns:
            QuerySet
        """
        today = date.today()
        return self.filter(
            Q(start_date__lte=today) & Q(end_date__gte=today)
        )

    def get_by_date_range(self, start_date: date = None, end_date: date = None):
        """
        기간별 프로젝트 조회

        Args:
            start_date: 시작일
            end_date: 종료일

        Returns:
            QuerySet
        """
        queryset = self.get_queryset()

        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)

        return queryset


class ProjectCompanyLinkRepository(GenericRepository):
    """
    ProjectCompanyLink Repository
    """
    model = ProjectCompanyLink
    serializer_class = ProjectCompanyLinkModelSerializer

    def get_by_project(self, project_id: int):
        """프로젝트별 회사 연결 조회"""
        return self.filter(Q(project_id=project_id))

    def get_by_role(self, role: str):
        """역할별 프로젝트-회사 연결 조회"""
        return self.filter(Q(role=role))

    def get_by_company(self, company_id: int):
        """회사별 프로젝트 연결 조회"""
        return self.filter(Q(company_id=company_id))


class ProjectAssigneeRepository(GenericRepository):
    """
    ProjectAssignee Repository
    """
    model = ProjectAssignee
    serializer_class = ProjectAssigneeModelSerializer

    def get_by_project(self, project_id: int):
        """프로젝트별 담당자 조회"""
        return self.filter(Q(project_id=project_id))

    def get_primary_assignee(self, project_id: int):
        """프로젝트의 주요 담당자 조회"""
        return self.filter(Q(project_id=project_id, is_primary=True)).first()

    def get_by_user(self, user_id: int):
        """사용자별 프로젝트 할당 조회"""
        return self.filter(Q(user_id=user_id))