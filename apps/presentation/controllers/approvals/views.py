"""
Approvals ViewSet

Approvals 도메인의 API 엔드포인트를 제공합니다.
"""
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.decorators import action

from apps.infrastructure.views.mixins import StandardViewSetMixin
from apps.infrastructure.responses.swagger_api_response import ApiResponse
from apps.infrastructure.responses.success import SuccessResponse
from apps.infrastructure.responses.error import ValidationErrorResponse
from apps.domain.approvals.models import ApprovalRequest, ApprovalLine, ApprovalPolicy, ApprovalPolicyStep
from apps.infrastructure.serializers.approvals import (
    ApprovalRequestModelSerializer,
    ApprovalLineModelSerializer,
    ApprovalPolicyModelSerializer,
    ApprovalPolicyStepModelSerializer, ApprovalLineRejectInputSerializer, ApprovalLineApproveInputSerializer,
)
from apps.application.leave_aprroval.usecase import LeaveApprovalUseCase


@extend_schema(tags=['Approval'])
class ApprovalRequestViewSet(StandardViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    ApprovalRequest ViewSet

    결재 요청 조회를 제공합니다.
    """
    queryset = ApprovalRequest.objects.all()
    serializer_class = ApprovalRequestModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        queryset = ApprovalRequest.objects.filter(deleted_at__isnull=True)

        requester_id = self.request.query_params.get('requester_id')
        status = self.request.query_params.get('status')
        request_type = self.request.query_params.get('request_type')

        if requester_id:
            queryset = queryset.filter(requester_id=requester_id)
        if status:
            queryset = queryset.filter(status=status)
        if request_type:
            queryset = queryset.filter(request_type=request_type)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
            OpenApiParameter("requester_id", int, OpenApiParameter.QUERY),
            OpenApiParameter("status", str, OpenApiParameter.QUERY),
            OpenApiParameter("request_type", str, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """결재 요청 목록 조회"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """결재 요청 상세 조회"""
        return super().retrieve(request, *args, **kwargs)


@extend_schema(tags=['Approval'])
class ApprovalLineViewSet(StandardViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    ApprovalLine ViewSet

    결재 라인 조회를 제공합니다.
    """
    queryset = ApprovalLine.objects.all()
    serializer_class = ApprovalLineModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        queryset = ApprovalLine.objects.filter(deleted_at__isnull=True)

        approval_request_id = self.request.query_params.get('approval_request_id')
        approver_id = self.request.query_params.get('approver_id')
        status = self.request.query_params.get('status')

        if approval_request_id:
            queryset = queryset.filter(approval_request_id=approval_request_id)
        if approver_id:
            queryset = queryset.filter(approver_id=approver_id)
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('step_order')

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
            OpenApiParameter("approval_request_id", int, OpenApiParameter.QUERY),
            OpenApiParameter("status", str, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """결재 라인 목록 조회"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """결재 라인 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=ApprovalLineApproveInputSerializer,
        responses=ApiResponse[dict]
    )
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """결재 라인 승인"""
        instance = self.get_object()
        approval_line, leave_request = LeaveApprovalUseCase.approve_leave_request(
            approver_line_id=instance.id,
            approver_user_id=request.user.id,
            comment=request.data.get('comment')
        )
        return SuccessResponse(
            data=self.get_serializer(approval_line).data,
            message="결재가 승인되었습니다."
        )

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=ApprovalLineRejectInputSerializer,
        responses=ApiResponse[dict]
    )
    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """결재 라인 반려"""
        instance = self.get_object()
        comment = request.data.get('comment')
        if not comment:
            return ValidationErrorResponse(
                message="반려 사유는 필수입니다."
            )

        approval_line, leave_request = LeaveApprovalUseCase.reject_leave_request(
            approval_line_id=instance.id,
            approval_user_id=request.user.id,
            comment=comment
        )
        return SuccessResponse(
            data=self.get_serializer(approval_line).data,
            message="결재가 반려되었습니다."
        )


@extend_schema(tags=['Approval'])
class ApprovalPolicyViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    ApprovalPolicy ViewSet

    결재 정책에 대한 CRUD 작업을 제공합니다.
    """
    queryset = ApprovalPolicy.objects.all()
    serializer_class = ApprovalPolicyModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        return ApprovalPolicy.objects.filter(deleted_at__isnull=True)

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """결재 정책 목록 조회"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """결재 정책 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=ApprovalPolicyModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """결재 정책 생성"""
        return super().create(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """결재 정책 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """결재 정책 삭제"""
        return super().destroy(request, *args, **kwargs)


@extend_schema(tags=['Approval'])
class ApprovalPolicyStepViewSet(StandardViewSetMixin, viewsets.ModelViewSet):
    """
    ApprovalPolicyStep ViewSet

    결재 정책 단계에 대한 CRUD 작업을 제공합니다.
    """
    queryset = ApprovalPolicyStep.objects.all()
    serializer_class = ApprovalPolicyStepModelSerializer

    def get_queryset(self):
        """QuerySet을 반환합니다."""
        queryset = ApprovalPolicyStep.objects.filter(deleted_at__isnull=True)

        policy_id = self.request.query_params.get('policy_id')
        if policy_id:
            queryset = queryset.filter(policy_id=policy_id)

        return queryset.order_by('step_order')

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY),
            OpenApiParameter("policy_id", int, OpenApiParameter.QUERY),
        ],
        responses=ApiResponse[dict]
    )
    def list(self, request, *args, **kwargs):
        """결재 정책 단계 목록 조회"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def retrieve(self, request, *args, **kwargs):
        """결재 정책 단계 상세 조회"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=ApprovalPolicyStepModelSerializer,
        responses=ApiResponse[dict]
    )
    def create(self, request, *args, **kwargs):
        """결재 정책 단계 생성"""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        request=ApprovalPolicyStepModelSerializer,
        responses=ApiResponse[dict]
    )
    def partial_update(self, request, *args, **kwargs):
        """결재 정책 단계 부분 수정"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", int, OpenApiParameter.PATH),
        ],
        responses=ApiResponse[dict]
    )
    def destroy(self, request, *args, **kwargs):
        """결재 정책 단계 삭제"""
        return super().destroy(request, *args, **kwargs)