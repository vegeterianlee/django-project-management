"""
Company Repository Implementation

model과 serializer_class만 지정하면 모든 CRUD가 자동으로 동작합니다.
"""
from django.db.models import Q

from apps.infrastructure.repositories.generic import GenericRepository
from apps.domain.company.models import Company, ContactPerson
from apps.infrastructure.serializers.company import (
    CompanyModelSerializer,
    ContactPersonModelSerializer,
)


class CompanyRepository(GenericRepository):
    """
    Company Repository

    model과 serializer_class만 지정하면 GenericRepository의 모든 기능을 사용할 수 있습니다.
    """
    model = Company
    serializer_class = CompanyModelSerializer

    def get_by_type(self, company_type: str):
        """
        회사 타입으로 조회하는 커스텀 메서드

        Args:
            company_type: 회사 타입 (CLIENT, DESIGN, CONSTRUCTION)

        Returns:
            QuerySet
        """
        return self.filter(Q(type=company_type))


class ContactPersonRepository(GenericRepository):
    """
    ContactPerson Repository
    """
    model = ContactPerson
    serializer_class = ContactPersonModelSerializer

    def get_by_company(self, company_id: int):
        """회사 ID로 연락 담당자 조회"""
        return self.filter(Q(company_id=company_id))

    def get_primary_contact(self, company_id: int):
        """회사의 주요 연락 담당자 조회"""
        return self.filter(Q(company_id=company_id, is_primary=True)).first()