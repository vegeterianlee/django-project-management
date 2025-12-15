"""
Notifications Domain Service

알림 도메인의 비즈니스 로직을 처리하는 서비스입니다.
"""
from typing import List, Optional
from django.db import models
from django.utils import timezone
from apps.domain.notifications.models import Notification
from apps.domain.users.models import User
from apps.infrastructure.exceptions.exceptions import ValidationException


class NotificationService:
    """
    알림 관련 비즈니스 로직을 처리하는 서비스입니다.

    책임:
    - 알림 생성
    - 알림 읽음 처리
    - 알림 조회
    """

    @staticmethod
    def create_notification(
        sender_id: int,
        receiver_id: int,
        notification_type: str,
        message: str,
        notification_type_id: Optional[int] = None
    ):
        """
        Args:
            sender_id: 발신자 ID
            receiver_id: 수신자 ID
            notification_type: 알림 타입
            message: 알림 메시지
            notification_type_id: 알림 타입별 ID (예: LeaveRequest.id, ApprovalRequest.id)

        Returns:
            Notification: 생성된 알림
        """

        # 발신자와 수신자가 같은 경우, 알림 생성하지 않음
        if sender_id == receiver_id:
            return None

        notification = Notification(
            sender_id=sender_id,
            receiver_id=receiver_id,
            notification_type=notification_type,
            notification_type_id=notification_type_id,
            message=message
        )

        return notification

    @staticmethod
    def create_bulk_notifications(
        sender_id: int,
        receiver_ids: List[int],
        notification_type: str,
        message: str,
        notification_type_id: Optional[int] = None
    ) -> List[Notification]:
        """
       여러 수신자에게 알림을 일괄 생성합니다.

       Args:
           sender_id: 발신자 ID
           receiver_ids: 수신자 ID 목록
           notification_type: 알림 타입
           message: 알림 메시지
           notification_type_id: 알림 타입별 ID

       Returns:
           List[Notification]: 생성된 알림 목록
       """
        notifications = []
        for receiver_id in receiver_ids:
            # 발신자와 수신자가 다른 경우에만 보냄
            if sender_id != receiver_id:
                notification = Notification(
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    notification_type=notification_type,
                    message=message,
                    notification_type_id=notification_type_id
                )
                notifications.append(notification)
        if notifications:
            Notification.objects.bulk_create(notifications)

        return notifications


    @staticmethod
    def mark_as_read(notification_id: int, user_id: int) -> Notification:
        """
        알림을 읽음으로 표시합니다.

        Args:
            notification_id: 알림 ID
            user_id: 사용자 ID (수신자 확인용)

        Returns:
            Notification: 읽음 처리된 알림
        """
        notification = Notification.objects.get(
            id=notification_id,
            deleted_at__isnull=True,
        )

        # 수신자 확인
        if notification.sender_id != user_id:
            raise ValidationException("본인의 알림만 읽음 처리할 수 있습니다.")

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])

        return notification

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        """
        사용자의 미읽음 알림 개수를 조회합니다.

        Args:
            user_id: 사용자 ID

        Returns:
            int: 미읽음 알림 개수
        """
        return Notification.objects.filter(
            receiver_id=user_id,
            is_read=False,
            deleted_at__isnull=True
        ).count()

    @staticmethod
    def get_unread_notifications(user_id: int) -> List[Notification]:
        """
        사용자의 미읽음 알림을 조회합니다.

        Args:
            user_id: 사용자 ID

        Returns:
            미읽음 알림 목록
        """
        return Notification.objects.filter(
            receiver_id=user_id,
            is_read=False,
            deleted_at__isnull=True
        ).order_by("-created_at")