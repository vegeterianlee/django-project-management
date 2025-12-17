"""
Custom Permission 클래스
특정 엔드포인트는 인증 없이 접근 허용
"""
from rest_framework import permissions
from rest_framework.request import Request

class IsAuthenticatedOrPublic(permissions.BasePermission):
    """
    인증이 필요하지만, 특정 공개 엔드포인트는 제외

    설계 목적:
    - 전역적으로 인증을 요구하되, 로그인/healthcheck 등은 제외
    - ViewSet 레벨에서 authentication_classes = []로 오버라이드 불필요하게 하는 게 목표
    - URL 패턴 기반으로 자동 판단
    """

    # 인증 없이 접근 가능한 URL 패턴 목록
    PUBLIC_ENDPOINTS = [
        '/api/auth/login',
        '/api/auth/refresh',
        '/api/healthcheck',
        '/api/schema/',  # Swagger 스키마
        '/api/docs/',  # Swagger UI
    ]

    def has_permission(self, request: Request, view) -> bool:
        """
        요청 경로를 확인하여 인증 필요 여부 결정

        Args:
            request: HTTP 요청 객체
            view: ViewSet 또는 APIView

        Returns:
            bool: 권한 허용 여부
        """
        path = request.path

        # 공개 엔드포인트인지 확인
        for public_endpoint in self.PUBLIC_ENDPOINTS:
            if path.startswith(public_endpoint):
                return True

        # 그 외 모든 엔드포인트는 인증 필요
        return request.user and request.user.is_authenticated

