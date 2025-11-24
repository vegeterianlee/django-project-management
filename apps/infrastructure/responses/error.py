"""
Error Response Classes

에러 응답을 위한 Response 클래스들입니다.
"""
from rest_framework import status
from .base import BaseJsonResponse


class BadRequestResponse(BaseJsonResponse):
    """
    잘못된 요청 응답

    400 Bad Request에 사용합니다.
    """

    def __init__(self, data=None, message="잘못된 요청입니다.", key="bad_request"):
        super().__init__(
            data=data,
            message=message,
            code=status.HTTP_400_BAD_REQUEST,
            key=key
        )


class ConflictResponse(BaseJsonResponse):
    """
    충돌 응답
    409 Conflict에 사용합니다.
    """

    def __init__(self, data=None, message="Conflict!", key="conflict"):
        super().__init__(
            data=data,
            message=message,
            code=status.HTTP_409_CONFLICT,
            key=key
        )


class UnauthorizedResponse(BaseJsonResponse):
    """
    인증 실패 응답

    401 Unauthorized에 사용합니다.
    """

    def __init__(self, data=None, message="접근 권한이 없습니다.", key="unauthorized"):
        super().__init__(
            data=data,
            message=message,
            code=status.HTTP_401_UNAUTHORIZED,
            key=key
        )


class PermissionDeniedResponse(BaseJsonResponse):
    """
    권한 거부 응답

    403 Forbidden에 사용합니다.
    """

    def __init__(self, data=None, message="접근이 제한되었습니다.", key="permission_denied"):
        super().__init__(
            data=data,
            message=message,
            code=status.HTTP_403_FORBIDDEN,
            key=key
        )


class NotFoundResponse(BaseJsonResponse):
    """
    리소스 없음 응답

    404 Not Found에 사용합니다.
    """

    def __init__(self, data=None, message="해당 데이터를 찾을 수 없습니다.", key="not_found"):
        super().__init__(
            data=data,
            message=message,
            code=status.HTTP_404_NOT_FOUND,
            key=key
        )



class ValidationErrorResponse(BaseJsonResponse):
    """
    검증 오류 응답

    Serializer 검증 실패 시 사용합니다.
    """

    def __init__(self, data=None, message="데이터 검증에 실패했습니다.", key="validation_error"):
        super().__init__(
            data=data,
            message=message,
            code=status.HTTP_400_BAD_REQUEST,
            key=key
        )


class ServerErrorResponse(BaseJsonResponse):
    """
    서버 오류 응답

    500 Internal Server Error에 사용합니다.
    """

    def __init__(self, data=None, message="서버 내부에서 오류가 발생했습니다.", key="server_error"):
        super().__init__(
            data=data,
            message=message,
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            key=key
        )