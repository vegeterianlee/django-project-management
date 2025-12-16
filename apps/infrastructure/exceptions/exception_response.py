"""
Exception to Response Converter

예외를 표준화된 API Response로 변환하는 헬퍼 함수들입니다.
"""
from rest_framework import status

from apps.infrastructure.exceptions.exceptions import BaseCustomException, EntityNotFoundException, ValidationException, \
    EntityDeleteRestrictedException, EntityDeleteProtectedException, PermissionDeniedException
from apps.infrastructure.responses.error import NotFoundResponse, ValidationErrorResponse, PermissionDeniedResponse, \
    ConflictResponse, BadRequestResponse


def exception_to_response(exc: BaseCustomException):
    """
    BaseCustomException을 적절한 Response로 변환합니다.

    Args:
        exc: 변환할 예외 인스턴스

    Returns:
        BaseJsonResponse: 표준화된 응답
    """
    # 예외 타입에 따라 적절한 Response 선택
    if isinstance(exc, EntityNotFoundException):
        return NotFoundResponse(
            data=exc.errors,
            message=str(exc.detail) if hasattr(exc, 'detail') else exc.key,
            key=exc.key
        )
    elif isinstance(exc, ValidationException):
        return ValidationErrorResponse(
            data=exc.errors,
            message=str(exc.detail) if hasattr(exc, 'detail') else exc.key,
            key=exc.key
        )
    elif isinstance(exc, PermissionDeniedException):
        return PermissionDeniedResponse(
            data=exc.errors,
            message=str(exc.detail) if hasattr(exc, 'detail') else exc.key,
            key=exc.key
        )
    elif isinstance(exc, (EntityDeleteRestrictedException, EntityDeleteProtectedException)):
        return ConflictResponse(
            data=exc.errors,
            message=str(exc.detail) if hasattr(exc, 'detail') else exc.key,
            key=exc.key
        )
    else:
        # 기본적으로 status_code에 따라 변환
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            return NotFoundResponse(
                data=exc.errors,
                message=str(exc.detail) if hasattr(exc, 'detail') else exc.message,
                key=exc.key
            )
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            return PermissionDeniedResponse(
                data=exc.errors,
                message=str(exc.detail) if hasattr(exc, 'detail') else exc.message,
                key=exc.key
            )
        elif exc.status_code == status.HTTP_409_CONFLICT:
            return ConflictResponse(
                data=exc.errors,
                message=str(exc.detail) if hasattr(exc, 'detail') else exc.message,
                key=exc.key
            )
        else:
            return BadRequestResponse(
                data=exc.errors,
                message=str(exc.detail) if hasattr(exc, 'detail') else exc.message,
                key=exc.key
            )