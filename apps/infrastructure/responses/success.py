"""
Success Response Classes

성공 응답을 위한 Response 클래스들입니다.
"""
from rest_framework import status
from .base import BaseJsonResponse


class SuccessResponse(BaseJsonResponse):
    """
    일반 성공 응답

    GET, PUT, PATCH 등의 성공 응답에 사용합니다.
    """

    def __init__(self, data=None, message="조회에 성공했습니다.", key="success"):
        super().__init__(
            data=data,
            message=message,
            code=status.HTTP_200_OK,
            key=key
        )


class CreatedResponse(BaseJsonResponse):
    """
    생성 성공 응답

    POST 요청으로 리소스가 성공적으로 생성되었을 때 사용합니다.
    """

    def __init__(self, data=None, message="데이터가 생성되었습니다.", key="created"):
        super().__init__(
            data=data,
            message=message,
            code=status.HTTP_201_CREATED,
            key=key
        )

class UpdatedResponse(BaseJsonResponse):
    """
    변경 성공 응답

    PUT 요청으로 리소스가 성공적으로 변경되었을 때 사용합니다.
    """

    def __init__(self, data=None, message="데이터가 변경되었습니다.", key="updated"):
        super().__init__(
            data=data,
            message=message,
            code=status.HTTP_201_CREATED,
            key=key
        )


class NoContentResponse(BaseJsonResponse):
    """
    내용 없음 응답

    DELETE 요청 성공 시 사용합니다.
    """

    def __init__(self, message="데이터가 삭제되었습니다.", key="deleted"):
        super().__init__(
            data=None,
            message=message,
            code=status.HTTP_204_NO_CONTENT,
            key=key
        )