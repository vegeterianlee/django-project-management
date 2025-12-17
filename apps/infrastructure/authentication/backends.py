"""
Custom Authentication Backend
JWT 토큰을 검증하여 User 객체를 반환
"""
from typing import Optional
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class JWTAuthenticationBackend(BaseAuthentication):
    """
    JWT 토큰 기반 인증 Backend

    설계 목적
    - Django authentication 시스템과 통합
    - request.user로 User 객체 접근 가능
    - DRF permission 클래스와 연동
    """

    def authenticate(self, request) -> Optional[tuple]:
        """
        JWT 토큰을 검증하고 User 객체를 반환

        :param request: HTTP 요청 객체
        :return: tuple (User, token) 또는 None
        """

        # Authorization 헤더에서 JWT 토큰 추출
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            #raise AuthenticationFailed('Authorization 헤더에 JWT 토큰이 없습니다.')
            return None # 인증 시도 없는 것으로 진행

        token = auth_header.split(' ')[1]
        try:
            # JWT 토큰 검증
            validated_token = UntypedToken(token)
            #print("token", token)
            #print("validated_token", validated_token)

            # 토큰에서 user_id 추출
            user_id = validated_token.get('user_id')
            if not user_id:
                raise AuthenticationFailed('토큰의 payload에서 유저 아이디를 찾을 수 없습니다.')
            try:
                user = User.objects.get(id=user_id, deleted_at__isnull=True)
            except User.DoesNotExist:
                raise AuthenticationFailed('토큰의 payload에서 사용자를 조회할 수 없습니다.')

            # 계정 잠금 확인
            if user.account_locked:
                raise AuthenticationFailed('계정이 잠겨있습니다.')

            return (user, token)

        except TokenError as e:
            raise AuthenticationFailed("유효하지 않은 토큰 입니다.")

        except Exception as e:
            print(e)
            raise AuthenticationFailed("인증 중 오류가 발생했습니다.")