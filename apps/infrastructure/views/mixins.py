"""
ViewSet Mixins

모든 ViewSet에서 사용할 수 있는 범용 Mixin 클래스들입니다.
"""
from rest_framework import viewsets, status

from apps.infrastructure.responses.error import BadRequestResponse, ValidationErrorResponse, NotFoundResponse
from apps.infrastructure.responses.success import SuccessResponse, CreatedResponse, NoContentResponse, UpdatedResponse


class StandardResponseMixin:
    """
    표준화된 API Response를 제공하는 Mixin

    모든 ViewSet에서 이 Mixin을 상속받으면 일관된 응답 형식을 사용할 수 있습니다.
    """

    def finalize_response(self, request, response, *args, **kwargs):
        """
        응답을 최종 처리합니다.

        DRF의 기본 응답을 표준화된 형식으로 변환합니다.
        """
        # 이미 BaseJsonResponse인 경우 그대로 반환
        if isinstance(response, SuccessResponse) or isinstance(response, CreatedResponse):
            return response

        # DRF Response를 표준 형식으로 변환
        if hasattr(response, 'data'):
            if response.status_code == status.HTTP_201_CREATED:
                return CreatedResponse(data=response.data)
            elif response.status_code == status.HTTP_204_NO_CONTENT:
                return NoContentResponse()
            elif response.status_code >= 400:
                return BadRequestResponse(data=response.data)
            else:
                return SuccessResponse(data=response.data)

        return response


class StandardViewSetMixin(StandardResponseMixin):
    """
    표준화된 ViewSet Mixin

    CRUD 작업에 대한 표준 응답을 제공합니다.

    상속 구조:
    StandardViewSetMixin
    └── StandardResponseMixin
    └── viewsets.ModelViewSet (실제 사용 시)
        └── CreateModelMixin (create 메서드)
        └── RetrieveModelMixin (retrieve 메서드) ← super().retrieve()가 여기 호출
        └── ListModelMixin (list 메서드) ← super().list()가 여기 호출
        └── UpdateModelMixin (update, partial_update 메서드)
        └── DestroyModelMixin (destroy 메서드)
    """

    def list(self, request, *args, **kwargs):
        """
        리스트 조회

        super().list()는 MRO에서 다음 클래스인 viewsets.ModelViewSet의
        list 메서드를 호출하며, 이는 ListModelMixin.list()를 실행합니다.
        """
        # super()는 MRO에서 다음 클래스인 viewsets.ModelViewSet을 가리킴
        # ModelViewSet.list() → ListModelMixin.list() 실행
        response = super().list(request, *args, **kwargs)
        return SuccessResponse(data=response.data)

    def retrieve(self, request, *args, **kwargs):
        """단일 조회"""
        try:
            response = super().retrieve(request, *args, **kwargs)
            return SuccessResponse(data=response.data)
        except Exception as e:
            return NotFoundResponse(message=str(e))

    def create(self, request, *args, **kwargs):
        """생성"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            return CreatedResponse(
                data=self.get_serializer(instance).data,
                message="생성되었습니다."
            )
        return ValidationErrorResponse(
            data=serializer.errors,
            message="검증에 실패했습니다."
        )

    def update(self, request, *args, **kwargs):
        """전체 업데이트"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            return UpdatedResponse(
                data=self.get_serializer(instance).data,
                message="Updated Successfully!"
            )
        return ValidationErrorResponse(
            data=serializer.errors,
            message="Validation Failed!"
        )

    def partial_update(self, request, *args, **kwargs):
        """부분 업데이트"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            instance = serializer.save()
            return UpdatedResponse(
                data=self.get_serializer(instance).data,
                message="수정되었습니다."
            )
        return ValidationErrorResponse(
            data=serializer.errors,
            message="검증에 실패했습니다."
        )

    def destroy(self, request, *args, **kwargs):
        """삭제"""
        instance = self.get_object()
        instance.delete()
        return NoContentResponse(message="삭제되었습니다.")