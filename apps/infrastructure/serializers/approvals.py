from apps.domain.approvals.models import ApprovalPolicyStep, ApprovalPolicy
from rest_framework import serializers


class ApprovalPolicyStepModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalPolicyStep
        fields = ['id', 'policy', 'step_order', 'approver_selector_type', ...]

    def validate(self, data):
        # step_order 중복 검증 (unique_together로도 처리 가능)
        return data


class ApprovalPolicyModelSerializer(serializers.ModelSerializer):
    steps = ApprovalPolicyStepModelSerializer(many=True, read_only=True)

    class Meta:
        model = ApprovalPolicy
        fields = ['id', 'request_type', 'applies_to_dept_type', 'applies_to_role', 'steps', ...]