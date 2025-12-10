"""
Users Serializers

Users 도메인의 모델을 직렬화/역직렬화하는 Serializer입니다.
"""
from rest_framework import serializers
from apps.domain.users.models import (
    User,
    Department,
    Position,
    UserPermission,
    PhaseAccessRule,
)


class DepartmentModelSerializer(serializers.ModelSerializer):
    """Department 모델의 Serializer"""

    class Meta:
        model = Department
        fields = ['id', 'name', 'organization_type', 'parent_department', 'description']
        read_only_fields = ['id']


class PositionModelSerializer(serializers.ModelSerializer):
    """Position 모델의 Serializer"""

    class Meta:
        model = Position
        fields = [
            'id',
            'title',
            'description',
            'hierarchy_level',
            'is_executive',
        ]
        read_only_fields = ['id']


class UserModelSerializer(serializers.ModelSerializer):
    """
    User 모델의 Serializer

    User 모델의 모든 필드를 직렬화/역직렬화합니다.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'user_uid',
            'name',
            'email',
            'position_id',
            'department_id',
            'company',
            'company_name',
            'profile_url',
            'color',
            'password',
            'account_locked',
            'login_attempts',
            'lock_time',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'deleted_at',
            'company_name',
        ]
        extra_kwargs = {
            'password': {'write_only': True},  # 비밀번호는 쓰기 전용
        }

    def validate_email(self, value):
        """이메일 형식 검증"""
        if '@' not in value:
            raise serializers.ValidationError("올바른 이메일 형식이 아닙니다.")
        return value

    def validate_user_uid(self, value):
        """user_uid 중복 검증"""
        # 업데이트 시에는 현재 인스턴스 제외
        if self.instance:
            if User.objects.filter(user_uid=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("이미 사용 중인 user_uid입니다.")
        else:
            if User.objects.filter(user_uid=value).exists():
                raise serializers.ValidationError("이미 사용 중인 user_uid입니다.")
        return value


class UserPermissionModelSerializer(serializers.ModelSerializer):
    """UserPermission 모델의 Serializer"""
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = UserPermission
        fields = [
            'id',
            'user',
            'user_name',
            'phase',
            'permission_type',
        ]
        read_only_fields = ['id', 'user_name']

    def validate(self, data):
        """사용자, Phase, 권한 타입의 조합이 고유한지 검증"""
        user = data.get('user') or (self.instance.user if self.instance else None)
        phase = data.get('phase') or (self.instance.phase if self.instance else None)
        permission_type = data.get('permission_type') or (self.instance.permission_type if self.instance else None)

        if user and phase and permission_type:
            queryset = UserPermission.objects.filter(
                user=user,
                phase=phase,
                permission_type=permission_type
            )
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError(
                    "이미 존재하는 사용자-Phase-권한 타입 조합입니다."
                )

        return data


class PhaseAccessRuleModelSerializer(serializers.ModelSerializer):
    """PhaseAccessRule 모델의 Serializer"""

    class Meta:
        model = PhaseAccessRule
        fields = [
            'id',
            'phase',
            'required_departments',
        ]
        read_only_fields = ['id']

    def validate_phase(self, value):
        """Phase 값 검증"""
        valid_phases = [choice[0] for choice in PhaseAccessRule.PHASE_CHOICES]
        if value not in valid_phases:
            raise serializers.ValidationError(
                f"Phase는 {valid_phases} 중 하나여야 합니다."
            )
        return value

    def validate_required_departments(self, value):
        """required_departments가 리스트인지 검증"""
        if not isinstance(value, list):
            raise serializers.ValidationError("required_departments는 리스트여야 합니다.")
        return value