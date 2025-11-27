"""
Company ViewSet

Company 도메인의 API 엔드포인트를 제공합니다.
StandardViewSetMixin을 사용하여 표준화된 응답 형식을 자동으로 사용합니다.
"""
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.decorators import action


from apps.infrastructure.responses.error import NotFoundResponse

from apps.infrastructure.repositories.company.repository import CompanyRepository, ContactPersonRepository
from apps.infrastructure.responses.swagger_api_response import ApiResponse
from apps.infrastructure.views.mixins import StandardViewSetMixin
from apps.domain.company.models import Company, ContactPerson
from apps.infrastructure.serializers.company import (
    CompanyModelSerializer,
    ContactPersonModelSerializer,
)
from apps.infrastructure.responses.success import SuccessResponse


@extend_schema(tags=['Company'])
class CompanyViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    Company ViewSet

    Company 모델에 대한 CRUD 작업을 제공합니다.
    StandardViewSetMixin을 상속받아 표준화된 응답 형식을 자동으로 사용합니다.
    """
    queryset = Company.objects.all()
    serializer_class = CompanyModelSerializer

    # ← 이 메서드가 있으면 항상 이것이 호출됨
    def get_queryset(self):
        """
        QuerySet을 반환합니다.
        소프트 삭제된 항목은 자동으로 제외됩니다 (TimeStampedSoftDelete).
        """
        return Company.objects.filter(deleted_at__isnull=True)

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """회사 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """회사 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=CompanyModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """회사 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=CompanyModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """회사 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=CompanyModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """회사 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """회사 삭제"""
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("company_type", str, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-type/(?P<company_type>[^/.]+)')
    def by_type(self, request, company_type=None):
        """
        회사 타입으로 조회하는 커스텀 액션

        GET /api/companies/by-type/CLIENT/
        """
        #print(CompanyViewSet.mro())
        repository = CompanyRepository()
        companies = repository.get_by_type(company_type)
        serializer = self.get_serializer(companies, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")


@extend_schema(tags=['ContactPerson'])
class ContactPersonViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    ContactPerson ViewSet

    ContactPerson 모델에 대한 CRUD 작업을 제공합니다.
    """
    queryset = ContactPerson.objects.all()
    serializer_class = ContactPersonModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        return ContactPerson.objects.filter(deleted_at__isnull=True)

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """연락 담당자 목록 조회 (페이지네이션 적용)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """연락 담당자 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=ContactPersonModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """연락 담당자 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=ContactPersonModelSerializer,
        responses=ApiResponse[dict]
    )
    def update(self, request, *args, **kwargs):
        """연락 담당자 수정"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=ContactPersonModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """연락 담당자 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """연락 담당자 삭제"""
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("company_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='by-company/(?P<company_id>[^/.]+)')
    def by_company(self, request, company_id=None):
        """
        회사 ID로 연락 담당자 조회

        GET /api/contact-persons/by-company/1/
        """
        repository = ContactPersonRepository()
        contact_persons = repository.get_by_company(int(company_id))
        serializer = self.get_serializer(contact_persons, many=True)
        return SuccessResponse(data=serializer.data, message="조회되었습니다.")

    @extend_schema(
        parameters=[
            OpenApiParameter("company_id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='primary/(?P<company_id>[^/.]+)')
    def primary_contact(self, request, company_id=None):
        """
        회사의 주요 연락 담당자 조회

        GET /api/contact-persons/primary/1/
        """
        repository = ContactPersonRepository()
        contact_person = repository.get_primary_contact(int(company_id))
        if contact_person:
            serializer = self.get_serializer(contact_person)
            return SuccessResponse(data=serializer.data, message="조회되었습니다.")
        return NotFoundResponse(message="주요 연락 담당자를 찾을 수 없습니다.")