"""
Sales Repository Implementation

model과 serializer_class만 지정하면 모든 CRUD가 자동으로 동작합니다.
복잡한 쿼리는 커스텀 메서드로 구현합니다.
"""
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal

from apps.infrastructure.repositories.generic import GenericRepository
from apps.domain.sales.models import ProjectSales, SalesAssignee, SalesHistory
from apps.infrastructure.serializers.sales import (
    ProjectSalesModelSerializer,
    SalesAssigneeModelSerializer,
    SalesHistoryModelSerializer,
)


class ProjectSalesRepository(GenericRepository):
    """
    ProjectSales Repository

    model과 serializer_class만 지정하면 GenericRepository의 모든 기능을 사용할 수 있습니다.
    """
    model = ProjectSales
    serializer_class = ProjectSalesModelSerializer

    def get_by_project(self, project_id: int):
        """
        프로젝트별 영업 조회

        Args:
            project_id: 프로젝트 ID

        Returns:
            QuerySet
        """
        return self.filter(Q(project_id=project_id))

    def get_by_sales_type(self, sales_type: str):
        """
        영업 유형별 조회

        Args:
            sales_type: 영업 유형

        Returns:
            QuerySet
        """
        return self.filter(Q(sales_type=sales_type))

    def get_by_date_range(self, start_date: date, end_date: date):
        """
        날짜 범위별 영업 조회 (영업 접수일 기준)

        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            QuerySet
        """
        return self.filter(
            Q(sales_received_date__gte=start_date) & Q(sales_received_date__lte=end_date)
        )

    def get_by_assignee(self, user_id: int):
        """
        담당자별 영업 조회 (SalesAssignee를 통한)

        Args:
            user_id: 사용자 ID

        Returns:
            QuerySet
        """
        # SalesAssignee를 통해 연결된 영업 조회
        sales_ids = SalesAssignee.objects.filter(
            user_id=user_id,
            deleted_at__isnull=True
        ).values_list('sales_id', flat=True)

        return self.filter(Q(id__in=sales_ids))

    def get_by_amount_range(self, min_amount: Decimal, max_amount: Decimal):
        """
        금액 범위별 영업 조회 (견적 금액 기준)

        Args:
            min_amount: 최소 금액
            max_amount: 최대 금액

        Returns:
            QuerySet
        """
        return self.filter(
            Q(estimate_amount__gte=min_amount) & Q(estimate_amount__lte=max_amount)
        )


class SalesAssigneeRepository(GenericRepository):
    """
    SalesAssignee Repository
    """
    model = SalesAssignee
    serializer_class = SalesAssigneeModelSerializer

    def get_by_sales(self, sales_id: int):
        """영업별 담당자 조회"""
        return self.filter(Q(sales_id=sales_id))

    def get_primary_assignee(self, sales_id: int):
        """영업의 주요 담당자 조회"""
        return self.filter(Q(sales_id=sales_id, is_primary=True)).first()

    def get_by_user(self, user_id: int):
        """사용자별 영업 할당 조회"""
        return self.filter(Q(user_id=user_id))


class SalesHistoryRepository(GenericRepository):
    """
    SalesHistory Repository
    """
    model = SalesHistory
    serializer_class = SalesHistoryModelSerializer

    def get_by_sales(self, sales_id: int):
        """영업별 이력 조회"""
        return self.filter(Q(sales_id=sales_id))

    def get_by_user(self, user_id: int):
        """사용자별 영업 이력 조회"""
        return self.filter(Q(user_id=user_id))

    def get_public_histories(self, sales_id: int):
        """영업의 공개 이력 조회"""
        return self.filter(Q(sales_id=sales_id, is_public=True))

    def get_private_histories(self, sales_id: int):
        """영업의 비공개 이력 조회"""
        return self.filter(Q(sales_id=sales_id, is_public=False))