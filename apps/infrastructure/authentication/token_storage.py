"""
Redis를 이용한 Refresh Token 저장/조회 서비스
"""
import json
from typing import Optional
from django.conf import settings
from django.core.cache import cache
import redis

class RefreshTokenStorage:
    """
    Redis를 이용한 Refresh Token 저장 및 관리

    구조:
    - Refresh Token은 메모리 저장소에 저장
    - Access Token은 JWT로 클랑이언트에 저장
    - TTL 설정으로 자동 만료 처리
    """

    REDIS_PREFIX = "refresh_token:"
    DEFAULT_TTL = 60 * 60 * 24 * 7

    def __init__(self):
        redis_url = settings.JWT_REDIS_URL
        self.redis_client = redis.from_url(redis_url, decode_responses=True)


    def save_refresh_token(self, user_id: int, refresh_token: str, ttl: int = None) -> bool:
        """
        Refresh Token을 Redis에 저장

        :param user_id:
        :param refresh_token:
        :param ttl:
        :return:
        """
        key = f"{self.REDIS_PREFIX}{user_id}"
        ttl = ttl or self.DEFAULT_TTL

        try:
            value = json.dumps({
                "user_id": user_id,
                "refresh_token": refresh_token
            })
            self.redis_client.setex(key, ttl, value)
            return True
        except Exception as e:
            return False

    def get_refresh_token(self, user_id: int) -> Optional[str]:
        """
        사용자 ID로 Refresh Token 조회
        :param user_id:
        :return:
        """
        key = f"{self.REDIS_PREFIX}{user_id}"
        try:
            value = self.redis_client.get(key)
            if value:
                data = json.loads(value)
                return data.get("refresh_token")
            return None
        except Exception as e:
            return None

    def delete_refresh_token(self, user_id: int) -> bool:
        """
        Refresh Token 삭제 (로그아웃 시)
        :param user_id:
        :return:
        """
        key = f"{self.REDIS_PREFIX}{user_id}"
        try:
            self.redis_client.delete(key)
            return True
        except Exception:
            return False

    def verify_refresh_token(self, user_id: int, refresh_token: str) -> bool:
        """
        Refresh Token 검증

        Args:
            user_id: 사용자 ID
            refresh_token: 검증할 Refresh Token

        Returns:
            bool: 검증 성공 여부
        """
        stored_token = self.get_refresh_token(user_id)
        return stored_token == refresh_token




