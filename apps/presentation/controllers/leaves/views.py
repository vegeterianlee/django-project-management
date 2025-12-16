"""
Leaves ViewSet

Leaves 도메인의 API 엔드포인트를 제공합니다.
"""
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from django.db.models import Q

from apps.infrastructure.views.mixins import StandardViewSetMixin
from apps.infrastructure.responses.swagger_api_response import ApiResponse
from apps.infrastructure.responses.success import SuccessResponse, CreatedResponse
from apps.infrastructure.responses.error import ValidationErrorResponse, NotFoundResponse
from apps.domain.leaves.models import LeaveRequest, LeaveGrant, LeaveUsage
from apps.infrastructure.serializers.leaves import (
    LeaveRequestModelSerializer,
    LeaveGrantModelSerializer,
    LeaveUsageModelSerializer,
)
from apps.application.leave_aprroval.usecase import LeaveApprovalUseCase
from apps.infrastructure.exceptions.exceptions import ValidationException


@extend_schema(tags=['Leave'])
class LeaveRequestViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    LeaveRequest ViewSet

    휴가 신청에 대한 CRUD 작업을 제공합니다.
    """
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        queryset = LeaveRequest.objects.filter(deleted_at__isnull=True)

        # 필터링 옵션
        user_id = self.request.query_params.get('user_id')
        status = self.request.query_params.get('status')
        leave_type = self.request.query_params.get('leave_type')

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if status:
            queryset = queryset.filter(status=status)
        if leave_type:
            queryset = queryset.filter(leave_type=leave_type)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
            OpenApiParameter("user_id", int, OpenApiParameter.QUERY),
            OpenApiParameter("status", str, OpenApiParameter.QUERY),
            OpenApiParameter("leave_type", str, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """휴가 신청 목록 조회"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """휴가 신청 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=LeaveRequestModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """휴가 신청 생성"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        leave_request, approval_request = LeaveApprovalUseCase.create_leave_request_with_approval(
            user_id=request.user.id,
            leave_type=serializer.validated_data['leave_type'],
            start_date=serializer.validated_data['start_date'].isoformat(),
            end_date=serializer.validated_data['end_date'].isoformat(),
            total_days=float(serializer.validated_data['total_days']),
            reason=serializer.validated_data['reason'],
            delegate_user_id=serializer.validated_data['delegate_user'].id
        )

        return CreatedResponse(
            data=self.get_serializer(leave_request).data,
            message='휴가 신청이 생성되었습니다.'
        )

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=LeaveRequestModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """휴가 신청 부분 수정 (승인 전에만 가능)"""
        instance = self.get_object()

        # 승인된 경우 수정 불가
        if instance.status == 'APPROVED':
            return ValidationErrorResponse(
                message="승인된 휴가 신청은 수정할 수 없습니다."
            )

        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, *args, **kwargs):
        """휴가 신청 삭제 (취소)"""
        instance = self.get_object()

        if not instance.approval_request:
            from apps.infrastructure.responses.error import ValidationErrorResponse
            return ValidationErrorResponse(
                message="결재 요청이 없는 휴가 신청입니다."
            )

        approval_request, leave_request = LeaveApprovalUseCase.cancel_leave_request_with_approval(
            approval_request_id=instance.approval_request.id,
            cancelled_by_user_id=request.user.id,
            cancel_reason=request.data.get('cancel_reason', '사용자 요청')
        )

        return SuccessResponse(
            data=self.get_serializer(instance).data,
            message="휴가 신청이 취소되었습니다."
        )


@extend_schema(tags=['Leave'])
class LeaveGrantViewSet(StandardViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    LeaveGrant ViewSet

    휴가 지급 정보 조회를 제공합니다.
    """
    queryset = LeaveGrant.objects.all()
    serializer_class = LeaveGrantModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        queryset = LeaveGrant.objects.filter(deleted_at__isnull=True)

        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
            OpenApiParameter("user_id", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """휴가 지급 목록 조회"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """휴가 지급 상세 조회"""
        return super().retrieve(request, *args, **kwargs)


@extend_schema(tags=['Leave'])
class LeaveUsageViewSet(StandardViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    LeaveUsage ViewSet

    휴가 사용 정보 조회를 제공합니다.
    """
    queryset = LeaveUsage.objects.all()
    serializer_class = LeaveUsageModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        queryset = LeaveUsage.objects.filter(deleted_at__isnull=True)

        user_id = self.request.query_params.get('user_id')
        leave_request_id = self.request.query_params.get('leave_request_id')

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if leave_request_id:
            queryset = queryset.filter(leave_request_id=leave_request_id)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
            OpenApiParameter("user_id", int, OpenApiParameter.QUERY),
            OpenApiParameter("leave_request_id", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """휴가 사용 목록 조회"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """휴가 사용 상세 조회"""
        return super().retrieve(request, *args, **kwargs)