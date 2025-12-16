"""
Notifications Serializers

Notifications 도메인의 모델을 직렬화/역직렬화하는 Serializer입니다.
"""
from rest_framework import serializers
from apps.domain.notifications.models import Notification


class NotificationModelSerializer(serializers.ModelSerializer):
    """
    Notification 모델의 Serializer

    알림 정보를 직렬화/역직렬화합니다.
    """
    sender_name = serializers.CharField(source='sender.name', read_only=True)
    receiver_name = serializers.CharField(source='receiver.name', read_only=True)
    notification_type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True
    )

    class Meta:
        model = Notification
        fields = [
            'id',
            'sender',
            'sender_name',
            'receiver',
            'receiver_name',
            'notification_type',
            'notification_type_display',
            'notification_type_id',
            'message',
            'is_read',
            'read_at',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'deleted_at',
            'sender_name',
            'receiver_name',
            'notification_type_display',
            'read_at',
        ]

    def validate_notification_type(self, value):
        """알림 타입 검증"""
        valid_types = [choice[0] for choice in Notification.NOTIFICATION_TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"알림 타입은 {valid_types} 중 하나여야 합니다."
            )
        return value