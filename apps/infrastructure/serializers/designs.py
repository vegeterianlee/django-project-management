"""
Design Serializers

Design 도메인의 모델을 직렬화/역직렬화하는 Serializer입니다.
"""
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from typing import List, Dict, Any
from apps.domain.designs.models import ProjectDesign, DesignVersion, DesignAssignee, DesignHistory


class DesignAssigneeModelSerializer(serializers.ModelSerializer):
    """
    DesignAssignee 모델의 Serializer

    설계 담당자 정보를 직렬화/역직렬화합니다.
    """
    design_project_name = serializers.CharField(source='design.project.name', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = DesignAssignee
        fields = [
            'id',
            'design',
            'design_project_name',
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
            'design_project_name',
            'user_name',
            'user_email',
        ]

    def validate(self, data):
        """전체 필드 검증"""
        design = data.get('design') or (self.instance.design if self.instance else None)
        user = data.get('user') or (self.instance.user if self.instance else None)
        is_primary = data.get('is_primary', False) if self.instance is None else data.get('is_primary', self.instance.is_primary)

        # 같은 설계에 같은 사용자가 이미 존재하는지 확인
        if design and user:
            existing = DesignAssignee.objects.filter(
                design=design,
                user=user,
                deleted_at__isnull=True
            )
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError({
                    'user': '이 설계에 이미 할당된 사용자입니다.'
                })

        # 주요 담당자가 여러 명이면 안됨
        if is_primary and design:
            existing_primary = DesignAssignee.objects.filter(
                design=design,
                is_primary=True,
                deleted_at__isnull=True
            )
            if self.instance:
                existing_primary = existing_primary.exclude(id=self.instance.id)
            if existing_primary.exists():
                raise serializers.ValidationError({
                    'is_primary': '이 설계에 이미 주요 담당자가 존재합니다.'
                })

        return data


class DesignHistoryModelSerializer(serializers.ModelSerializer):
    """
    DesignHistory 모델의 Serializer

    설계 이력 정보를 직렬화/역직렬화합니다.
    """
    design_project_name = serializers.CharField(source='design.project.name', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True, allow_null=True)

    class Meta:
        model = DesignHistory
        fields = [
            'id',
            'design',
            'design_project_name',
            'user',
            'user_name',
            'content',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'deleted_at',
            'design_project_name',
            'user_name',
        ]


class DesignVersionModelSerializer(serializers.ModelSerializer):
    """
    DesignVersion 모델의 Serializer

    설계 버전 정보를 직렬화/역직렬화합니다.
    """
    design_project_name = serializers.CharField(source='design.project.name', read_only=True)

    class Meta:
        model = DesignVersion
        fields = [
            'id',
            'design',
            'design_project_name',
            'name',
            'status',
            'submitted_date',
            'construction_cost',
            'pile_quantity',
            'pile_length',
            'concrete_volume',
            'pc_length',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'deleted_at',
            'design_project_name',
        ]

    def validate_status(self, value):
        """상태 검증"""
        if value not in [choice[0] for choice in DesignVersion.STATUS_CHOICES]:
            raise serializers.ValidationError('유효하지 않은 상태입니다.')
        return value

    def validate(self, data):
        """전체 필드 검증"""
        design = data.get('design') or (self.instance.design if self.instance else None)
        name = data.get('name') or (self.instance.name if self.instance else None)

        # 같은 설계에 같은 이름의 버전이 이미 존재하는지 확인
        if design and name:
            existing = DesignVersion.objects.filter(
                design=design,
                name=name,
                deleted_at__isnull=True
            )
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError({
                    'name': '이 설계에 이미 같은 이름의 버전이 존재합니다.'
                })

        return data


class ProjectDesignModelSerializer(serializers.ModelSerializer):
    """
    ProjectDesign 모델의 Serializer

    프로젝트 설계 정보를 직렬화/역직렬화합니다.
    """
    versions = serializers.SerializerMethodField()
    versions_count = serializers.SerializerMethodField()
    assignees = serializers.SerializerMethodField()
    assignees_count = serializers.SerializerMethodField()
    histories = serializers.SerializerMethodField()
    histories_count = serializers.SerializerMethodField()

    class Meta:
        model = ProjectDesign
        fields = [
            'id',
            'project',
            'design_start_date',
            'design_folder_location',
            'versions',
            'versions_count',
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
            'versions',
            'versions_count',
            'assignees',
            'assignees_count',
            'histories',
            'histories_count',
        ]

    @extend_schema_field(
        serializers.ListField(
            child=serializers.DictField()
        )
    )
    def get_versions(self, obj: ProjectDesign) -> List[Dict[str, Any]]:
        """
        설계 버전 목록을 반환합니다.
        """
        versions = obj.versions.filter(deleted_at__isnull=True)
        return [
            {
                'id': version.id,
                'name': version.name,
                'status': version.status,
                'status_display': version.get_status_display(),
                'submitted_date': version.submitted_date.isoformat() if version.submitted_date else None,
                'construction_cost': str(version.construction_cost) if version.construction_cost else None,
            }
            for version in versions
        ]

    @extend_schema_field(serializers.IntegerField())
    def get_versions_count(self, obj: ProjectDesign) -> int:
        """
        설계 버전 수를 반환합니다.
        """
        return obj.versions.filter(deleted_at__isnull=True).count()

    @extend_schema_field(
        serializers.ListField(
            child=serializers.DictField()
        )
    )
    def get_assignees(self, obj: ProjectDesign) -> List[Dict[str, Any]]:
        """
        설계 담당자 목록을 반환합니다.
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
    def get_assignees_count(self, obj: ProjectDesign) -> int:
        """
        설계 담당자 수를 반환합니다.
        """
        return obj.assignees.filter(deleted_at__isnull=True).count()

    @extend_schema_field(
        serializers.ListField(
            child=serializers.DictField()
        )
    )
    def get_histories(self, obj: ProjectDesign) -> List[Dict[str, Any]]:
        """
        설계 이력 목록을 반환합니다.
        """
        histories = obj.histories.filter(deleted_at__isnull=True)
        return [
            {
                'id': history.id,
                'user_id': history.user.id if history.user else None,
                'user_name': history.user.name if history.user else None,
                'content': history.content,
                'created_at': history.created_at.isoformat() if history.created_at else None,
            }
            for history in histories
        ]

    @extend_schema_field(serializers.IntegerField())
    def get_histories_count(self, obj: ProjectDesign) -> int:
        """
        설계 이력 수를 반환합니다.
        """
        return obj.histories.filter(deleted_at__isnull=True).count()