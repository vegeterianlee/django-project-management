from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException
from apps.infrastructure.exceptions.exceptions import BaseCustomException
from apps.infrastructure.responses.error import NotFoundResponse, PermissionDeniedResponse, BadRequestResponse, \
    ServerErrorResponse, ValidationErrorResponse, UnauthorizedResponse, ConflictResponse


def custom_exception_handler(exc, context):
    """
       커스텀 예외 핸들러

       모든 예외를 표준화된 API Response 형태로 변환합니다.

       Args:
           exc: 발생한 예외
           context: 예외 발생 컨텍스트 (view, request 등)

       Returns:
           BaseJsonResponse: 표준화된 응답 형식
       """
    # DRF의 기본 예외 핸들러 실행
    response = exception_handler(exc, context)
    #print(response)

    # BaseCustomException인 경우
    if isinstance(exc, BaseCustomException):
        # 예외 타입에 따라 적절한 Response 클래스 선택
        error_data = exc.errors if exc.errors is not None else {"detail": str(exc.detail) if hasattr(exc, 'detail') else str(exc)}
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            return NotFoundResponse(
                data=error_data,
                message=str(exc.detail) if hasattr(exc, 'detail') else exc.key,
                key=exc.key
            )
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            return PermissionDeniedResponse(
                data=error_data,
                message=str(exc.detail) if hasattr(exc, 'detail') else exc.key,
                key=exc.key
            )
        elif exc.status_code == status.HTTP_409_CONFLICT:
            return ConflictResponse(
                data=error_data,
                message=str(exc.detail) if hasattr(exc, 'detail') else exc.key,
                key=exc.key
            )
        elif exc.status_code == status.HTTP_400_BAD_REQUEST:
            return BadRequestResponse(
                data=error_data,
                message=str(exc.detail) if hasattr(exc, 'detail') else exc.key,
                key=exc.key
            )
        else:
            return ServerErrorResponse(
                data=error_data,
                message=str(exc.detail) if hasattr(exc, 'detail') else exc.key,
                key=exc.key
            )

    # DRF의 기본 예외 (ValidationError 등)
    elif response is not None:
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            # Serializer 검증 오류
            return ValidationErrorResponse(
                data=response.data,
                message="데이터 검증 시 오류가 발생했습니다."
            )
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            return UnauthorizedResponse(
                data=response.data,
                message="접근 권한이 필요합니다."
            )
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            return PermissionDeniedResponse(
                data=response.data,
                message="접근 권한이 없습니다."
            )
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            return NotFoundResponse(
                data=response.data,
                message="해당 데이터를 찾을 수 없습니다."
            )
        else:
            return BadRequestResponse(
                data=response.data,
                message=str(response.data) if response.data else "잘못된 요청입니다."
            )

        # Python 일반 예외 (예상치 못한 예외)
    elif isinstance(exc, Exception) and not isinstance(exc, APIException):
        return ServerErrorResponse(
            data={"error": str(exc), "args": exc.args},
            message="서버 내부에서 오류가 발생했습니다.",
            key="internal_server_error"
        )

    # 예외가 처리되지 않은 경우 None 반환 (DRF 기본 처리)
    return response