"""
Sales Serializers

Sales 도메인의 모델을 직렬화/역직렬화하는 Serializer입니다.
"""
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from typing import List, Dict, Any
from apps.domain.sales.models import ProjectSales, SalesAssignee, SalesHistory
from apps.domain.users.models import User


class SalesAssigneeModelSerializer(serializers.ModelSerializer):
    """
    SalesAssignee 모델의 Serializer

    영업 담당자 정보를 직렬화/역직렬화합니다.
    """
    sales_project_name = serializers.CharField(source='sales.project.name', read_only=True)
    sales_type = serializers.CharField(source='sales.type', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = SalesAssignee
        fields = [
            'id',
            'sales',
            'sales_project_name',
            'sales_type',
            'user',
            'user_name',
            'user_email',
            'is_primary',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'deleted_at',
            'sales_project_name',
            'sales_type',
            'user_name',
            'user_email',
        ]

    def validate(self, data):
        """전체 필드 검증"""
        sales = data.get('sales') or (self.instance.sales if self.instance else None)
        user = data.get('user') or (self.instance.user if self.instance else None)
        is_primary = data.get('is_primary', False) if self.instance is None else data.get('is_primary', self.instance.is_primary)

        # 같은 영업에 같은 사용자가 이미 존재하는지 확인
        if sales and user:
            existing = SalesAssignee.objects.filter(
                sales=sales,
                user=user,
                deleted_at__isnull=True
            )
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError({
                    'user': '이 영업에 이미 할당된 사용자입니다.'
                })

        # 주요 담당자가 여러 명이면 안됨
        if is_primary and sales:
            existing_primary = SalesAssignee.objects.filter(
                sales=sales,
                is_primary=True,
                deleted_at__isnull=True
            )
            if self.instance:
                existing_primary = existing_primary.exclude(id=self.instance.id)
            if existing_primary.exists():
                raise serializers.ValidationError({
                    'is_primary': '이 영업에 이미 주요 담당자가 존재합니다.'
                })

        return data


class SalesHistoryModelSerializer(serializers.ModelSerializer):
    """
    SalesHistory 모델의 Serializer

    영업 이력 정보를 직렬화/역직렬화합니다.
    """
    sales_project_name = serializers.CharField(source='sales.project.name', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True) if hasattr(User, 'name') else serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = SalesHistory
        fields = [
            'id',
            'sales',
            'sales_project_name',
            'user',
            'user_name',
            'content',
            'is_public',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'deleted_at',
            'sales_project_name',
            'user_name',
        ]


class ProjectSalesModelSerializer(serializers.ModelSerializer):
    """
    ProjectSales 모델의 Serializer

    프로젝트 영업 정보를 직렬화/역직렬화합니다.
    """
    assignees = serializers.SerializerMethodField()
    assignees_count = serializers.SerializerMethodField()
    histories = serializers.SerializerMethodField()
    histories_count = serializers.SerializerMethodField()

    class Meta:
        model = ProjectSales
        fields = [
            'id',
            'project',
            'sales_type',
            'sales_received_date',
            'estimate_request_date',
            'estimate_expected_date',
            'estimate_submit_date',
            'estimate_amount',
            'design_amount',
            'assignees',
            'assignees_count',
            'histories',
            'histories_count',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'deleted_at',
            'assignees',
            'assignees_count',
            'histories',
            'histories_count',
        ]

    def validate_sales_type(self, value):
        """영업 유형 검증"""
        if value and value not in [choice[0] for choice in ProjectSales.SALES_TYPE_CHOICES]:
            raise serializers.ValidationError('유효하지 않은 영업 유형입니다.')
        return value

    @extend_schema_field(
        serializers.ListField(
            child=serializers.DictField()
        )
    )
    def get_assignees(self, obj: ProjectSales) -> List[Dict[str, Any]]:
        """
        영업 담당자 목록을 반환합니다.
        """
        assignees = obj.assignees.filter(deleted_at__isnull=True)
        return [
            {
                'id': assignee.id,
                'user_id': assignee.user.id,
                'user_name': assignee.user.name,
                'user_email': assignee.user.email,
                'is_primary': assignee.is_primary,
            }
            for assignee in assignees
        ]

    @extend_schema_field(serializers.IntegerField())
    def get_assignees_count(self, obj: ProjectSales) -> int:
        """
        영업 담당자 수를 반환합니다.
        """
        return obj.assignees.filter(deleted_at__isnull=True).count()

    @extend_schema_field(
        serializers.ListField(
            child=serializers.DictField()
        )
    )
    def get_histories(self, obj: ProjectSales) -> List[Dict[str, Any]]:
        """
        영업 이력 목록을 반환합니다.
        """
        histories = obj.histories.filter(deleted_at__isnull=True)
        return [
            {
                'id': history.id,
                'user_id': history.user.id if history.user else None,
                'user_name': history.user.name if history.user else None,
                'content': history.content,
                'is_public': history.is_public,
                'created_at': history.created_at.isoformat() if history.created_at else None,
            }
            for history in histories
        ]

    @extend_schema_field(serializers.IntegerField())
    def get_histories_count(self, obj: ProjectSales) -> int:
        """
        영업 이력 수를 반환합니다.
        """
        return obj.histories.filter(deleted_at__isnull=True).count()