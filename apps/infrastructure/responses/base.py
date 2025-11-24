from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse


class BaseJsonResponse(JsonResponse):
    """
        기본 JSON Response 클래스

        모든 API 응답의 공통 구조를 제공합니다.
        {
            "success": bool,
            "key": str,
            "code": int,
            "message": str,
            "data": any
        }
        """

    def __init__(self, data, message, code, key, **kwargs):
        """
           BaseJsonResponse 초기화

           Args:
               data: 응답 데이터 (기본값: None)
               message: 응답 메시지 (기본값: "")
               code: HTTP 상태 코드 (기본값: 200)
               key: 응답 키 (에러 타입 식별용)
               **kwargs: JsonResponse에 전달할 추가 인자
       """

        self.data = data
        self.message = message
        self.code = code
        self.key = key

        super().__init__(
            data=self.prepare_data(),
            **kwargs,
            status=self.code,
            encoder=DjangoJSONEncoder  # Django 모델 인스턴스도 직렬화 가능
        )

    def prepare_data(self):
        return {
            "success": self.code < 400,  # 2xx, 3xx는 True, 4xx, 5xx는 False
            "key": self.key,
            "code": self.code,
            "message": self.message,
            "data": self.data,
        }
