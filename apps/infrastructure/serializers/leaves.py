"""
Leaves Serializers

Leaves 도메인의 모델을 직렬화/역직렬화하는 Serializer입니다.
"""
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from apps.domain.leaves.models import LeaveGrant, LeaveRequest, LeaveUsage
from decimal import Decimal

class LeaveGrantModelSerializer(serializers.ModelSerializer):
    """
    LeaveGrant 모델을 직렬화/역직렬화하는 Serializer입니다.
    휴가 지급 정보를 직렬/역직렬화 합니다.
    """

    user_name = serializers.CharField(source='user.name', read_only=True)
    grant_type_display = serializers.CharField(source='get_grant_type_display', read_only=True)
    class Meta:
        model = LeaveGrant
        fields = [
            'id',
            'user',
            'user_name',
            'grant_type',
            'grant_type_display',
            'total_days',
            'remaining_days',
            'granted_at',
            'expires_at',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = [
            'id',
            "user",
            'created_at',
            'updated_at',
            'deleted_at',
            'user_name',
            'grant_type_display',
        ]

    def validate_grant_type(self, value):
        """지급타입 검증"""
        valid_types = [choice[0] for choice in LeaveGrant.GRANT_TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"지급 타입은 {valid_types} 중 하나여야 합니다."
            )
        return value

    def validate(self, data):
        """전체 필드 검증"""
        total_days = data.get('total_days') or (self.instance.total_days if self.instance else None)
        remaining_days = data.get('remaining_days') or (self.instance.remaining_days if self.instance else None)

        if not total_days or not remaining_days:
            if remaining_days < 0:
                raise serializers.ValidationError({
                    'remaining_days': '남은 휴가 일수는 0 이상이어야 합니다.'
                })

            if remaining_days > total_days:
                raise serializers.ValidationError({
                    'remaining_days': '남은 휴가 일수는 지급된 휴가 일수보다 클 수 없습니다.'
                })

        return data


class LeaveRequestModelSerializer(serializers.ModelSerializer):
    """
    LeaveRequest 모델을 직렬화/역직렬화하는 Serializer입니다.

    휴가 신청 정보를 직렬/역직렬화 합니다.
    """

    user_name = serializers.CharField(source='user.name', read_only=True)
    delegate_user_name = serializers.SerializerMethodField()
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approval_status = serializers.SerializerMethodField()
    approval_request_id = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = [
            'id',
            'user',
            'user_name',
            'approval_request',
            'approval_request_id',
            'leave_type',
            'leave_type_display',
            'start_date',
            'end_date',
            'total_days',
            'reason',
            'delegate_user',
            'delegate_user_name',
            'status',
            'status_display',
            'approval_status',
            'submitted_at',
            'cancelled_at',
            'cancel_reason',
            'created_at',
            'updated_at',
            'deleted_at',
        ]

        read_only_fields = [
            'id',
            "user",
            'created_at',
            'updated_at',
            'deleted_at',
            'user_name',
            'delegate_user_name',
            'leave_type_display',
            'approval_request',
            'approval_request_id',
            'status',
            'status_display',
            'approval_status',
            'submitted_at',
            'cancelled_at',
        ]

    @extend_schema_field(
        serializers.ListField(
            child=serializers.CharField()
        )
    )
    def get_delegate_user_name(self, obj):
        """위임 사용자 이름 반환 (None 처리)"""
        return obj.delegate_user.name if obj.delegate_user else None

    @extend_schema_field(
        serializers.ListField(
            child=serializers.IntegerField()
        )
    )
    def get_approval_request_id(self, obj):
        """결재 요청 ID 반환 (None 처리)"""
        return obj.approval_request.id  if obj.approval_request else None

    @extend_schema_field(
        serializers.ListField(
            child=serializers.CharField()
        )
    )
    def get_approval_status(self, obj):
        """결재 상태 변환"""
        if obj.approval_request:
            return obj.approval_request.get_status_display()
        return "결재 사항을 확인할 수 없습니다."

    def validate_leave_type(self, value):
        """휴가 타입 검증"""
        valid_types = [choice[0] for choice in LeaveRequest.LEAVE_TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"휴가 타입은 {valid_types} 중 하나여야 합니다."
            )
        return value

    def validate_status(self, value):
        """상태 검증"""
        valid_statuses = [choice[0] for choice in LeaveRequest.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"상태는 {valid_statuses} 중 하나여야 합니다."
            )
        return value

    def validate(self, data):
        """전체 필드 검증"""
        start_date = data.get('start_date') or (self.instance.start_date if self.instance else None)
        end_date = data.get('end_date') or (self.instance.end_date if self.instance else None)
        leave_type = data.get('leave_type') or (self.instance.leave_type if self.instance else None)
        total_days = data.get('total_days') or (self.instance.total_days if self.instance else None)

        # 날짜 순서 검증
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'end_date': '종료일은 시작일보다 늦어야 합니다.'
            })

        # 반차 검증
        if leave_type in ['HALF_MORNING', 'HALF_AFTERNOON']:
            if start_date and end_date and start_date != end_date:
                raise serializers.ValidationError({
                    'end_date': '반차는 시작일과 종료일이 같아야 합니다.'
                })
            if total_days is not None:
                # Decimal로 변환하여 비교
                if isinstance(total_days, str):
                    total_days_decimal = Decimal(total_days)
                elif isinstance(total_days, Decimal):
                    total_days_decimal = total_days
                else:
                    total_days_decimal = Decimal(str(total_days))

                if total_days_decimal != Decimal('0.5'):
                    raise serializers.ValidationError({
                        'total_days': '반차는 0.5일만 신청 가능합니다.'
                    })
            # 반차는 여기서 반환
            return data

        # 연차 검증 (반차가 아닌 경우만)
        if total_days is not None and total_days <= 0:
            raise serializers.ValidationError({
                'total_days': '휴가 일수는 0보다 커야 합니다.'
            })

        # 연차의 경우 날짜 차이 검증
        if start_date and end_date and total_days:
            date_diff = (end_date - start_date).days + 1

            # Decimal 타입으로 변환하여 비교
            if isinstance(total_days, str):
                total_days_decimal = Decimal(total_days)
            elif isinstance(total_days, Decimal):
                total_days_decimal = total_days
            else:
                total_days_decimal = Decimal(str(total_days))

            # int와 Decimal 비교를 위해 둘 다 Decimal로 변환
            date_diff_decimal = Decimal(str(date_diff))

            if date_diff_decimal != total_days_decimal:
                raise serializers.ValidationError({
                    'total_days': f'연차의 시작일과 종료일의 차이({date_diff}일)는 요청 휴가 일수({total_days_decimal}일)와 같아야 합니다.'
                })

            return data


class LeaveUsageModelSerializer(serializers.ModelSerializer):
    """
    LeaveUsage 모델의 Serializer

    휴가 사용 정보를 직렬화/역직렬화합니다.
    """
    user_name = serializers.CharField(source='user.name', read_only=True)
    leave_grant_id = serializers.IntegerField(source='leave_grant.id', read_only=True)
    leave_request_id = serializers.IntegerField(source='leave_request.id', read_only=True)

    class Meta:
        model = LeaveUsage
        fields = [
            'id',
            'user',
            'user_name',
            'leave_grant',
            'leave_grant_id',
            'leave_request',
            'leave_request_id',
            'used_days',
            'used_date',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = [
            'id',
            "user",
            'created_at',
            'updated_at',
            'deleted_at',
            'user_name',
            'leave_grant_id',
            'leave_request_id',
        ]

    def validate_used_days(self, value):
        """사용 일수 검증"""
        if value <= 0:
            raise serializers.ValidationError("사용 일수는 0보다 커야 합니다.")
        return value
