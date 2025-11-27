"""
Generic Repository Implementation

참조 프로젝트 구조를 기반으로 Django의 Serializer를 활용하여 구현합니다.
"""
from uuid import UUID
from rest_framework.serializers import Serializer
from django.db.models import Q, QuerySet, Model
from django.db.models import ProtectedError, RestrictedError
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

from apps.infrastructure.exceptions.exceptions import EntityNotFoundException, MultipleObjectsReturnedException, \
    EntityDeleteRestrictedException, EntityDeleteProtectedException
from apps.application.interfaces.repositories.generic import IGenericRepository
from apps.application.dtos.base import BaseDto
from attrs import asdict


class GenericRepository(IGenericRepository):
    """
    Generic Repository 구현

    Django의 Serializer를 활용하여 DTO를 처리하고,
    QuerySet을 반환하여 Django의 장점을 최대한 활용합니다.
    """
    model: Model = None
    serializer_class: Serializer = None
    queryset: QuerySet = None
    raise_serializer_exception: bool = True

    def __init__(self, alias: str = "default", raise_serializer_exception: bool = True):
        """
        리포지토리 초기화

        Args:
            alias: 사용할 데이터베이스 별칭 (멀티 DB 환경에서 사용)
            raise_serializer_exception: Serializer 검증 실패 시 예외 발생 여부
        """
        if not self.model:
            raise ImproperlyConfigured("Repositories Should define a Model Property!")

        if not self.serializer_class:
            raise ImproperlyConfigured(
                "Repositories Should define a serializer_class Property!"
            )

        self._alias = alias
        self.raise_serializer_exception = raise_serializer_exception

        # queryset이 지정되지 않았으면 get_queryset()으로 생성
        if self.queryset is None:
            self.queryset = self.get_queryset()

    def get_queryset(self) -> QuerySet:
        """
        기본 QuerySet을 반환합니다.
        소프트 삭제가 있는 모델의 경우 deleted_at이 None인 것만 반환합니다.

        Returns:
            QuerySet
        """
        queryset = self.model.objects.using(self._alias)

        # deleted_at 필드가 있으면 소프트 삭제되지 않은 것만 반환
        if hasattr(self.model, 'deleted_at'):
            queryset = queryset.filter(deleted_at__isnull=True)

        return queryset

    def serialize(self, dto: BaseDto | list[BaseDto], many: bool = False) -> Serializer:
        """
        DTO를 Serializer로 변환합니다.

        Args:
            dto: 변환할 DTO 또는 DTO 리스트
            many: 여러 객체인지 여부

        Returns:
            Serializer 인스턴스
        """

        # 1단계: DTO를 딕셔너리로 변환
        if many:
            data = [asdict(value) for value in dto]
        else:
            data = asdict(dto)
        # 2단계: 딕셔너리를 Serializer에 전달
        # data={'id': 1, 'name': '테스트', ...}
        # → Serializer가 이 딕셔너리를 검증하고 모델로 변환
        serializer = self.serializer_class(data=data, many=many)

        # 3단계: 검증
        serializer.is_valid(raise_exception=self.raise_serializer_exception)
        return serializer

    def get(self, expression: Q) -> QuerySet:
        """
        조건에 맞는 단일 레코드를 조회합니다.

        Args:
            expression: Django Q 객체

        Returns:
            QuerySet (단일 인스턴스)

        Raises:
            EntityNotFoundException: 레코드가 없을 때
            MultipleObjectsReturnedException: 여러 레코드가 반환될 때
        """
        try:
            return self.queryset.get(expression)
        except self.model.DoesNotExist:
            raise EntityNotFoundException()
        except self.model.MultipleObjectsReturned:
            raise MultipleObjectsReturnedException()

    def filter(self, expression: Q) -> QuerySet:
        """
        조건에 맞는 레코드들을 조회합니다.

        Args:
            expression: Django Q 객체

        Returns:
            QuerySet
        """
        return self.queryset.filter(expression)

    def get_by_pk(self, pk: UUID | int) -> QuerySet:
        """
        Primary Key로 레코드를 조회합니다.

        Args:
            pk: Primary Key (UUID 또는 int)

        Returns:
            QuerySet (단일 인스턴스)
        """
        return self.get(Q(pk=pk))

    def get_list(self) -> QuerySet:
        """
        기본 QuerySet을 반환합니다.

        Returns:
            QuerySet
        """
        return self.queryset

    def get_all(self) -> QuerySet:
        """
        모든 레코드를 조회합니다.

        Returns:
            QuerySet
        """
        return self.model.objects.using(self._alias).all()

    def create(self, dto: BaseDto) -> QuerySet:
        """
        DTO를 사용하여 새로운 레코드를 생성합니다.

        Args:
            dto: 생성할 데이터를 담은 DTO

        Returns:
            생성된 모델 인스턴스
        """
        serializer = self.serialize(dto=dto)
        return serializer.save()

    def bulk_create(self, dtos: list[BaseDto]) -> QuerySet:
        """
        여러 DTO를 사용하여 일괄 생성합니다.

        Args:
            dtos: 생성할 데이터를 담은 DTO 리스트

        Returns:
            생성된 모델 인스턴스 리스트
        """
        serializer = self.serialize(dto=dtos, many=True)
        return serializer.save()

    def delete(self, expression: Q) -> QuerySet:
        """
        조건에 맞는 레코드를 삭제합니다.
        소프트 삭제가 가능한 모델은 소프트 삭제를 수행합니다.

        Args:
            expression: Django Q 객체

        Returns:
            삭제된 레코드 수와 타입 정보
        """
        queryset = self.filter(expression)

        # 소프트 삭제가 가능한 경우
        if hasattr(self.model, 'deleted_at'):
            return queryset.update(deleted_at=timezone.now())
        else:
            # 하드 삭제
            try:
                return queryset.delete()
            except RestrictedError:
                raise EntityDeleteRestrictedException()
            except ProtectedError:
                raise EntityDeleteProtectedException()

    def update(self, dto: BaseDto) -> QuerySet:
        """
        DTO를 사용하여 레코드를 전체 업데이트합니다.

        Args:
            dto: 업데이트할 데이터를 담은 DTO (id 필수)

        Returns:
            업데이트된 모델 인스턴스
        """
        from attrs import asdict

        instance = self.get_by_pk(dto.id)
        serializer = self.serializer_class(
            instance, data=asdict(dto), partial=False
        )
        serializer.is_valid(raise_exception=self.raise_serializer_exception)

        try:
            return serializer.save()
        except self.model.DoesNotExist:
            raise EntityNotFoundException()

    def partial_update(self, id: UUID | int, data: dict) -> QuerySet:
        """
        부분 업데이트를 수행합니다.

        Args:
            id: 업데이트할 레코드의 ID
            data: 업데이트할 필드와 값의 딕셔너리

        Returns:
            업데이트된 모델 인스턴스
        """
        instance = self.get_by_pk(id)
        serializer = self.serializer_class(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=self.raise_serializer_exception)

        try:
            return serializer.save()
        except self.model.DoesNotExist:
            raise EntityNotFoundException()