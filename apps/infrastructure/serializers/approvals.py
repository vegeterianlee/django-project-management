"""
Approvals Serializers

Approvals 도메인의 모델을 직렬화/역직렬화하는 Serializer입니다.
"""
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from apps.domain.approvals.models import ApprovalRequest, ApprovalLine, ApprovalPolicy, ApprovalPolicyStep
from apps.domain.enums.departments import ORGANIZATION_TYPE_CHOICES


class ApprovalLineApproveInputSerializer(serializers.Serializer):
    """결재 승인 입력 Serializer"""
    comment = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="결재 승인 멘트 (선택사항)"
    )


class ApprovalLineRejectInputSerializer(serializers.Serializer):
    """결재 반려 입력 Serializer"""
    comment = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="반려 사유 (필수)"
    )


class ApprovalPolicyStepModelSerializer(serializers.ModelSerializer):
    """
    ApprovalPolicyStep 모델의 Serializer
    """
    approver_selector_type_display = serializers.CharField(
        source='get_approver_selector_type_display',
        read_only=True
    )

    class Meta:
        model = ApprovalPolicyStep
        fields = [
            'id',
            'policy',
            'step_order',
            'approver_selector_type',
            'approver_selector_type_display',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'deleted_at',
            'approver_selector_type_display',
        ]

    def validate_approver_selector_type(self, value):
        """결재자 선택 타입 검증"""
        valid_types = [choice[0] for choice in ApprovalPolicyStep.APPROVER_SELECTOR_TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"결재자 선택 타입은 {valid_types} 중 하나여야 합니다."
            )
        return value

    def validate(self, data):
        """전체 필드 검증"""
        policy = data.get('policy') or (self.instance.policy if self.instance else None)
        step_order = data.get('step_order') or (self.instance.step_order if self.instance else None)

        if policy and step_order is not None:
            existing = ApprovalPolicyStep.objects.filter(
                policy=policy,
                step_order=step_order,
                deleted_at__isnull=True
            )
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError({
                    'step_order': f'이 정책에 step_order {step_order}가 이미 존재합니다.'
                })

        return data


class ApprovalPolicyModelSerializer(serializers.ModelSerializer):
    """
    ApprovalPolicy 모델의 Serializer
    """
    steps = ApprovalPolicyStepModelSerializer(many=True, read_only=True)
    request_type_display = serializers.CharField(source='get_request_type_display', read_only=True)

    class Meta:
        model = ApprovalPolicy
        fields = [
            'id',
            'request_type',
            'request_type_display',
            'applies_to_dept_type',
            'applies_to_role',
            'steps',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'deleted_at',
            'request_type_display',
            'steps',
        ]

    def validate_request_type(self, value):
        """요청 타입 검증"""
        valid_types = [choice[0] for choice in ApprovalPolicy.REQUEST_TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"요청 타입은 {valid_types} 중 하나여야 합니다."
            )
        return value

    def validate_applies_to_role(self, value):
        """적용 대상 역할 검증"""
        valid_roles = [choice[0] for choice in ApprovalPolicy.APPLIES_TO_ROLE]
        if value not in valid_roles:
            valid_roles_display = [f"{choice[0]} ({choice[1]})" for choice in ApprovalPolicy.APPLIES_TO_ROLE]
            raise serializers.ValidationError(
                f"적용 대상 역할은 {valid_roles} 중 하나여야 합니다. "
                f"유효한 선택지: {valid_roles_display}"
            )
        return value

    def validate_applies_to_dept_type(self, value):
        """적용 대상 부서 타입 검증"""
        valid_dept_types = [choice[0] for choice in ORGANIZATION_TYPE_CHOICES]
        if value not in valid_dept_types:
            valid_dept_types_display = [f"{choice[0]} ({choice[1]})" for choice in ORGANIZATION_TYPE_CHOICES]
            raise serializers.ValidationError(
                f"적용 대상 부서 타입은 {valid_dept_types} 중 하나여야 합니다. "
                f"유효한 선택지: {valid_dept_types_display}"
            )
        return value


class ApprovalLineModelSerializer(serializers.ModelSerializer):
    """
    ApprovalLine 모델의 Serializer

    결재 라인 정보를 직렬화/역직렬화합니다.
    """
    approver_name = serializers.CharField(source='approver.name', read_only=True)
    approver_email = serializers.CharField(source='approver.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approval_request_id = serializers.IntegerField(source='approval_request.id', read_only=True)

    class Meta:
        model = ApprovalLine
        fields = [
            'id',
            'approval_request',
            'approval_request_id',
            'step_order',
            'approver',
            'approver_name',
            'approver_email',
            'status',
            'status_display',
            'acted_at',
            'comment',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'deleted_at',
            'approver_name',
            'approver_email',
            'status_display',
            'approval_request_id',
            'acted_at',
        ]

    def validate_status(self, value):
        """상태 검증"""
        valid_statuses = [choice[0] for choice in ApprovalLine.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"상태는 {valid_statuses} 중 하나여야 합니다."
            )
        return value


class ApprovalRequestModelSerializer(serializers.ModelSerializer):
    """
    ApprovalRequest 모델의 Serializer

    결재 요청 정보를 직렬화/역직렬화합니다.
    """
    requester_name = serializers.CharField(source='requester.name', read_only=True)
    requester_email = serializers.CharField(source='requester.email', read_only=True)
    request_type_display = serializers.CharField(source='get_request_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approval_lines = ApprovalLineModelSerializer(many=True, read_only=True)
    leave_request_id = serializers.SerializerMethodField()

    class Meta:
        model = ApprovalRequest
        fields = [
            'id',
            'requester',
            'requester_name',
            'requester_email',
            'request_type',
            'request_type_display',
            'request_type_id',
            'status',
            'status_display',
            'submitted_at',
            'approved_at',
            'rejected_at',
            'cancelled_at',
            'approval_lines',
            'leave_request_id',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'deleted_at',
            'requester_name',
            'requester_email',
            'request_type_display',
            'status_display',
            'approval_lines',
            'leave_request_id',
            'submitted_at',
            'approved_at',
            'rejected_at',
            'cancelled_at',
        ]

    @extend_schema_field(
        serializers.ListField(
            child=serializers.IntegerField()
        )
    )
    def get_leave_request_id(self, obj):
        """LeaveRequest ID 반환 (LEAVE 타입인 경우)"""
        if obj.request_type == 'LEAVE':
            try:
                return obj.leave_request.id
            except:
                return None
        return None

    def validate_request_type(self, value):
        """요청 타입 검증"""
        valid_types = [choice[0] for choice in ApprovalRequest.REQUEST_TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"요청 타입은 {valid_types} 중 하나여야 합니다."
            )
        return value

    def validate_status(self, value):
        """상태 검증"""
        valid_statuses = [choice[0] for choice in ApprovalRequest.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"상태는 {valid_statuses} 중 하나여야 합니다."
            )
        return value