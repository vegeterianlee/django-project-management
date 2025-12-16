"""
Notifications ViewSet

Notifications 도메인의 API 엔드포인트를 제공합니다.
"""
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.decorators import action

from apps.infrastructure.views.mixins import StandardViewSetMixin
from apps.infrastructure.responses.swagger_api_response import ApiResponse
from apps.infrastructure.responses.success import SuccessResponse
from apps.domain.notifications.models import Notification
from apps.infrastructure.serializers.notifications import NotificationModelSerializer
from apps.domain.notifications.service import NotificationService


@extend_schema(tags=['Notification'])
class NotificationViewSet(StandardViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    Notification ViewSet

    알림 조회 및 읽음 처리를 제공합니다.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        queryset = Notification.objects.filter(
            deleted_at__isnull=True
        )

        is_read = self.request.query_params.get('is_read')
        notification_type = self.request.query_params.get('notification_type')
        receiver_id = self.request.query_params.get('receiver_id')

        if receiver_id is not None:
            queryset = queryset.filter(receiver_id=receiver_id)

        if is_read is not None:
            is_read_bool = is_read.lower() == 'true'
            queryset = queryset.filter(is_read=is_read_bool)
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        return queryset.order_by('-created_at')

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
            OpenApiParameter("is_read", str, OpenApiParameter.QUERY),
            OpenApiParameter("receiver_id", int, OpenApiParameter.QUERY),
            OpenApiParameter("notification_type", str, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """알림 목록 조회 (본인 알림만)"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """알림 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=True, methods=['post'], url_path='mark-as-read')
    def mark_as_read(self, request, pk=None):
        """알림 읽음 처리"""
        notification = NotificationService.mark_as_read(
            notification_id=int(pk),
            user_id=request.user.id
        )
        return SuccessResponse(
            data=self.get_serializer(notification).data,
            message="알림이 읽음 처리되었습니다."
        )

    @extend_schema(
        parameters=[
            OpenApiParameter("receiver_id", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['post'], url_path='mark-all-as-read')
    def mark_all_as_read(self, request):
        """본인의 모든 알림 읽음 처리"""
        count = NotificationService.mark_all_as_read(user_id=request.user.id)
        return SuccessResponse(
            data={'count': count},
            message=f"{count}개의 알림이 읽음 처리되었습니다."
        )

    @extend_schema(
        parameters=[
            OpenApiParameter("receiver_id", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """본인의 미읽음 알림 개수 조회"""
        count = NotificationService.get_unread_count(user_id=request.user.id)
        return SuccessResponse(
            data={'count': count}
        )

    @extend_schema(
        parameters=[
            OpenApiParameter("receiver_id", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=False, methods=['get'], url_path='unreads')
    def unread_list(self, request):
        """본인의 미읽음 알림 목록 조회"""
        notifications = NotificationService.get_unread_notifications(user_id=request.user.id)
        return SuccessResponse(
            data=self.get_serializer(notifications, many=True).data  # ✅ many=True 추가
        )