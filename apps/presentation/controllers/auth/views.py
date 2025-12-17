"""
인증 관련 View
로그인, 토큰 갱신, 로그아웃
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

from apps.domain.users.models import User
from apps.infrastructure.authentication.token_storage import RefreshTokenStorage
from apps.infrastructure.responses.success import SuccessResponse
from apps.infrastructure.responses.error import BadRequestResponse, UnauthorizedResponse
from apps.infrastructure.exceptions.exceptions import ValidationException, UnAuthorizedException, \
    PasswordMissmatchException, InvalidTokenException

class AuthViewSet(viewsets.ViewSet):
    """
    인증 관련 ViewSet
    """

    @extend_schema(
        tags=['Auth'],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'user_uid': {'type': '유저 아이디'},
                    'password': {'type': '비밀번호'},
                },
                'required': ['user_uid', 'password'],
            }
        },
        responses={200: dict}
    )
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        """
        로그인 및 JWT 토큰 발급
        :param request:
        :return:
        """
        user_uid = request.data.get('user_uid')
        password = request.data.get('password')

        if not user_uid or not password:
            raise ValidationException('유저 아이디와 비밀번호를 입력해주세요.')

        try:
            user = User.objects.get(user_uid=user_uid, deleted_at__isnull=True)
        except User.DoesNotExist:
            raise UnAuthorizedException("사용자를 찾을 수 없습니다.")

        if not user.check_password(password):
            # 로그인 시도 횟수 증가
            user.login_attempts += 1
            if user.login_attempts >= 5:
                user.account_locked = True
            user.save(update_fields=['login_attempts', 'account_locked'])
            raise PasswordMissmatchException("비밀번호가 틀렸습니다.")

        # 계정 잠금 확인
        if user.account_locked:
            raise UnAuthorizedException("계정이 잠겨있습니다.")

        # 로그인 성공
        user.login_attempts = 0
        if user.account_locked:
            user.account_locked = False
        user.save(update_fields=['login_attempts', "account_locked"])

        # JWT 토큰
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Refresh Token Redis에 저장
        token_storage = RefreshTokenStorage()
        token_storage.save_refresh_token(user.id, refresh_token)

        return SuccessResponse(
            data={
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'id': user.id,
                    'user_uid': user.user_uid,
                    'name': user.name,
                    'email': user.email,
                }
            },
            message='로그인 성공했습니다.'
        )

    @extend_schema(
        tags=['Auth'],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'refresh_token': {'type': 'string'},
                },
                'required': ['refresh_token'],
            }
        },
        responses={200: dict}
    )
    @action(detail=False, methods=['post'], url_path='refresh')
    def refresh(self, request):
        """
        Refresh Token으로 Access Token 갱신
        """
        refresh_token = request.data.get('refresh_token')

        if not refresh_token:
            raise InvalidTokenException("refresh 토큰이 없습니다.")

        try:
            # Refresh Token 검증
            refresh = RefreshToken(refresh_token)
            user_id = refresh.get('user_id')

            # Redis에서 Refresh Token 확인
            token_storage = RefreshTokenStorage()
            if not token_storage.verify_refresh_token(user_id, refresh_token):
                raise InvalidTokenException("refresh 토큰 정보가 올바르지 않습니다.")

            # 새로운 Access Token 발급
            new_access_token = str(refresh.access_token)

            return SuccessResponse(
                data={
                    'access_token': new_access_token,
                },
                message='토큰 갱신 성공했습니다.'
            )

        except TokenError:
            raise UnAuthorizedException("refresh 토큰이 만료되었습니다.")

    @extend_schema(
        tags=['Auth'],
        responses={200: dict}
    )
    @action(detail=False, methods=['post'], url_path='logout')
    def logout(self, request):
        """
        로그아웃 (Refresh Token 삭제)
        """
        if not request.user or not request.user.is_authenticated:
            raise UnAuthorizedException("로그인이 필요합니다.")

        # Redis에서 Refresh Token 삭제
        token_storage = RefreshTokenStorage()
        token_storage.delete_refresh_token(request.user.id)

        return SuccessResponse(
            message='로그아웃 성공'
        )