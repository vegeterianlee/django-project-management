"""
Design Repository Implementation

model과 serializer_class만 지정하면 모든 CRUD가 자동으로 동작합니다.
복잡한 쿼리는 커스텀 메서드로 구현합니다.
"""
from django.db.models import Q
from datetime import datetime, date


from apps.infrastructure.repositories.generic import GenericRepository
from apps.domain.designs.models import ProjectDesign, DesignVersion, DesignAssignee, DesignHistory
from apps.infrastructure.serializers.designs import (
    ProjectDesignModelSerializer,
    DesignVersionModelSerializer,
    DesignAssigneeModelSerializer,
    DesignHistoryModelSerializer,
)


class ProjectDesignRepository(GenericRepository):
    """
    ProjectDesign Repository

    model과 serializer_class만 지정하면 GenericRepository의 모든 기능을 사용할 수 있습니다.
    """
    model = ProjectDesign
    serializer_class = ProjectDesignModelSerializer

    def get_by_project(self, project_id: int):
        """
        프로젝트별 설계 조회

        Args:
            project_id: 프로젝트 ID

        Returns:
            QuerySet
        """
        return self.filter(Q(project_id=project_id))

    def get_by_date_range(self, start_date: date, end_date: date):
        """
        날짜 범위별 설계 조회 (설계 시작일 기준)

        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            QuerySet
        """
        return self.filter(
            Q(design_start_date__gte=start_date) & Q(design_start_date__lte=end_date)
        )

    def get_by_assignee(self, user_id: int):
        """
        담당자별 설계 조회 (DesignAssignee를 통한)

        Args:
            user_id: 사용자 ID

        Returns:
            QuerySet
        """
        # DesignAssignee를 통해 연결된 설계 조회
        design_ids = DesignAssignee.objects.filter(
            user_id=user_id,
            deleted_at__isnull=True
        ).values_list('design_id', flat=True)

        return self.filter(Q(id__in=design_ids))


class DesignVersionRepository(GenericRepository):
    """
    DesignVersion Repository
    """
    model = DesignVersion
    serializer_class = DesignVersionModelSerializer

    def get_by_design(self, design_id: int):
        """설계별 버전 조회"""
        return self.filter(Q(design_id=design_id))

    def get_by_status(self, status: str):
        """상태별 버전 조회"""
        return self.filter(Q(status=status))

    def get_by_design_and_status(self, design_id: int, status: str):
        """설계와 상태별 버전 조회"""
        return self.filter(Q(design_id=design_id, status=status))

    def get_by_date_range(self, start_date: date, end_date: date):
        """날짜 범위별 버전 조회 (제출일 기준)"""
        return self.filter(
            Q(submitted_date__gte=start_date) & Q(submitted_date__lte=end_date)
        )


class DesignAssigneeRepository(GenericRepository):
    """
    DesignAssignee Repository
    """
    model = DesignAssignee
    serializer_class = DesignAssigneeModelSerializer

    def get_by_design(self, design_id: int):
        """설계별 담당자 조회"""
        return self.filter(Q(design_id=design_id))

    def get_primary_assignee(self, design_id: int):
        """설계의 주요 담당자 조회"""
        return self.filter(Q(design_id=design_id, is_primary=True)).first()

    def get_by_user(self, user_id: int):
        """사용자별 설계 할당 조회"""
        return self.filter(Q(user_id=user_id))


class DesignHistoryRepository(GenericRepository):
    """
    DesignHistory Repository
    """
    model = DesignHistory
    serializer_class = DesignHistoryModelSerializer

    def get_by_design(self, design_id: int):
        """설계별 이력 조회"""
        return self.filter(Q(design_id=design_id))

    def get_by_user(self, user_id: int):
        """사용자별 설계 이력 조회"""
        return self.filter(Q(user_id=user_id))