"""
Projects Serializers

Projects 도메인의 모델을 직렬화/역직렬화하는 Serializer입니다.
"""
from typing import List, Dict, Any

from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from django.db import transaction
from rest_framework import serializers
from apps.domain.projects.models import Project, ProjectCompanyLink, ProjectAssignee, ProjectMethod


class ProjectMethodModelSerializer(serializers.ModelSerializer):
    """
    ProjectMethod 모델의 Serializer

    프로젝트-공법 연결 정보를 직렬화/역직렬화합니다.
    """
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = ProjectMethod
        fields = [
            'id',
            'project',
            'project_name',
            'method',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'deleted_at',
            'project_name',
        ]

    def validate_method(self, value):
        """공법 검증"""
        valid_methods = [choice[0] for choice in ProjectMethod.METHOD_CHOICES]
        if value not in valid_methods:
            raise serializers.ValidationError(
                f"공법은 {valid_methods} 중 하나여야 합니다."
            )
        return value

    def validate(self, data):
        """전체 필드 검증"""
        project = data.get('project') or (self.instance.project if self.instance else None)
        method = data.get('method') or (self.instance.method if self.instance else None)

        # 같은 프로젝트에 같은 공법이 이미 존재하는지 확인
        if project and method:
            existing = ProjectMethod.objects.filter(
                project=project,
                method=method,
                deleted_at__isnull=True
            )
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError({
                    'method': f'이 프로젝트에 {method} 공법이 이미 존재합니다.'
                })

        return data


class ProjectModelSerializer(serializers.ModelSerializer):
    """
    Project 모델의 Serializer

    Project 모델의 모든 필드를 직렬화/역직렬화합니다.
    역할별 company_links 분류, methods 목록, assignees 목록을 포함합니다.
    """
    # 역할별 company_links 분류
    company_links_by_role = serializers.SerializerMethodField()

    # methods 목록 (다중 공법 지원)
    methods = serializers.SerializerMethodField()

    # assignees 목록과 개수
    assignees = serializers.SerializerMethodField()
    assignees_count = serializers.SerializerMethodField()

    # 쓰기용: ListField (프로젝트 생성 시 methods를 받기 위해)
    methods_input = serializers.ListField(
        child=serializers.ChoiceField(choices=ProjectMethod.METHOD_CHOICES),
        write_only=True,
        required=False,
        help_text="공법 목록 (프로젝트 생성 시 함께 등록)"
    )

    class Meta:
        model = Project
        fields = [
            'id',
            'project_code',
            'name',
            'description',
            'status',
            'methods',  # 공법 목록 (상세 정보)
            'methods_input',  # 공법 입력 (쓰기 전용)
            'start_date',
            'end_date',
            'company_links_by_role',  # 역할별 분류된 company_links
            'assignees',  # 담당자 목록
            'assignees_count',  # 담당자 수
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'deleted_at',
            'company_links_by_role',
            'methods',
            'assignees',
            'assignees_count',
        ]

    @extend_schema_field(
        serializers.ListField(
            child=serializers.DictField()
        )
    )
    def get_methods(self, obj) -> List[Dict[str, Any]]:
        """
        프로젝트에 연결된 공법 목록을 반환합니다 (상세 정보).

        Args:
            obj: Project 인스턴스

        Returns:
            list: 공법 정보 리스트
        """
        # 소프트 삭제되지 않은 methods 조회
        methods = obj.methods.filter(deleted_at__isnull=True)

        result = []
        for method in methods:
            method_data = {
                'id': method.id,
                'method': method.method,
            }
            result.append(method_data)

        return result

    @extend_schema_field(
        serializers.DictField(
            child=serializers.ListField(
                child=serializers.DictField()
            )
        )
    )
    def get_company_links_by_role(self, obj) -> List[Dict[str, Any]]:
        """
        역할별로 분류된 company_links를 반환합니다.

        Args:
            obj: Project 인스턴스

        Returns:
            dict: {
                'CLIENT': [company_link1, company_link2, ...],
                'DESIGN': [company_link3, ...],
                'CONSTRUCTION': [company_link4, ...],
                'count': {
                    'CLIENT': 2,
                    'DESIGN': 1,
                    'CONSTRUCTION': 1,
                    'total': 4
                }
            }
        """
        # 소프트 삭제되지 않은 company_links 조회
        company_links = obj.company_links.filter(deleted_at__isnull=True)

        # 역할별로 분류
        result = {
            'CLIENT': [],
            'DESIGN': [],
            'CONSTRUCTION': [],
            'count': {
                'CLIENT': 0,
                'DESIGN': 0,
                'CONSTRUCTION': 0,
                'total': 0
            }
        }

        # 간단한 Company 정보를 포함한 Serializer 사용
        for link in company_links:
            link_data = {
                'id': link.id,
                'company_id': link.company.id,
                'company_name': link.company.name,
                'role': link.role,
                'created_at': link.created_at,
            }

            result[link.role].append(link_data)
            result['count'][link.role] += 1
            result['count']['total'] += 1

        return result

    def create(self, validated_data):
        """
        Project 생성 시 methods도 함께 생성

        Args:
            validated_data: 검증된 데이터

        Returns:
            Project: 생성된 Project 인스턴스
        """
        # methods_input을 validated_data에서 분리
        methods_data = validated_data.pop('methods_input', [])

        # ProjectMethod 생성
        with transaction.atomic():
            # Project 생성
            project = Project.objects.create(**validated_data)

            # ProjectMethod 일괄 생성
            if methods_data:
                project_methods = [
                    ProjectMethod(project=project, method=method)
                    for method in methods_data
                ]
                ProjectMethod.objects.bulk_create(project_methods)

        return project

    def update(self, instance, validated_data):
        """
        Project 업데이트 시 methods도 업데이트 (선택적)

        Args:
            instance: 업데이트할 Project 인스턴스
            validated_data: 검증된 데이터

        Returns:
            Project: 업데이트된 Project 인스턴스
        """
        # methods_input이 있으면 업데이트
        methods_data = validated_data.pop('methods_input', None)

        # Project 업데이트
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # methods_input이 제공된 경우에만 methods 업데이트
        if methods_data is not None:
            # 기존 methods 소프트 삭제 (실제로는 삭제하지 않고, 새로운 것만 추가)
            # 또는 기존 것을 유지하고 새로운 것만 추가하는 방식 선택 가능

            # 방법 1: 기존 methods를 모두 삭제하고 새로 생성
            # ProjectMethod.objects.filter(project=instance, deleted_at__isnull=True).update(deleted_at=timezone.now())

            # 방법 2: 기존 methods를 유지하고 새로운 것만 추가 (권장)
            existing_methods = set(
                ProjectMethod.objects.filter(
                    project=instance,
                    deleted_at__isnull=True
                ).values_list('method', flat=True)
            )

            new_methods = set(methods_data)

            # 추가할 methods
            to_add = new_methods - existing_methods
            for method in to_add:
                ProjectMethod.objects.create(project=instance, method=method)

            # 삭제할 methods (기존에는 있지만 새 리스트에는 없는 것)
            to_remove = existing_methods - new_methods
            if to_remove:
                ProjectMethod.objects.filter(
                    project=instance,
                    method__in=to_remove,
                    deleted_at__isnull=True
                ).update(deleted_at=timezone.now())

        return instance

    @extend_schema_field(
        serializers.ListField(
            child=serializers.DictField()
        )
    )
    def get_assignees(self, obj):
        """
        프로젝트에 할당된 담당자 목록을 반환합니다.

        Args:
            obj: Project 인스턴스

        Returns:
            list: 담당자 정보 리스트
        """
        # 소프트 삭제되지 않은 assignees 조회
        assignees = obj.assignees.filter(deleted_at__isnull=True)

        result = []
        for assignee in assignees:
            assignee_data = {
                'id': assignee.id,
                'user_id': assignee.user.id,
                'user_name': assignee.user.name,
                'user_email': assignee.user.email,
                'is_primary': assignee.is_primary,
                'created_at': assignee.created_at,
            }
            result.append(assignee_data)

        return result

    @extend_schema_field(serializers.IntegerField())
    def get_assignees_count(self, obj) -> int:
        """
        프로젝트에 할당된 담당자 수를 반환합니다.

        Args:
            obj: Project 인스턴스

        Returns:
            int: 담당자 수
        """
        return obj.assignees.filter(deleted_at__isnull=True).count()

    def validate_methods_input(self, value):
        """
        methods_input 필드 검증

        Args:
            value: 공법 리스트

        Returns:
            list: 검증된 공법 리스트
        """
        if not isinstance(value, list):
            raise serializers.ValidationError("methods_input은 리스트여야 합니다.")

        is_partial_update = self.instance is not None
        if len(value) == 0 and not is_partial_update:
            raise serializers.ValidationError("프로젝트 생성 시 공법은 포함되어야 합니다.")

        # 유효한 공법인지 확인
        valid_methods = [choice[0] for choice in ProjectMethod.METHOD_CHOICES]
        for method in value:
            if method not in valid_methods:
                raise serializers.ValidationError(
                    f"공법 '{method}'는 {valid_methods} 중 하나여야 합니다."
                )

        # 중복 제거 (중복이 있으면 에러 발생)
        if len(value) != len(set(value)):
            raise serializers.ValidationError("중복된 공법이 있습니다.")

        return value

    def validate_status(self, value):
        """상태 검증"""
        if value is None:
            return value
        valid_statuses = [choice[0] for choice in Project.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"프로젝트 상태는 {valid_statuses} 중 하나여야 합니다."
            )
        return value

    def validate(self, data):
        """전체 필드 검증"""
        start_date = data.get('start_date') or (self.instance.start_date if self.instance else None)
        end_date = data.get('end_date') or (self.instance.end_date if self.instance else None)

        # 시작일이 종료일보다 늦으면 안됨
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'end_date': '종료일은 시작일보다 늦어야 합니다.'
            })

        return data


class ProjectCompanyLinkModelSerializer(serializers.ModelSerializer):
    """
    ProjectCompanyLink 모델의 Serializer

    프로젝트-회사 연결 정보를 직렬화/역직렬화합니다.
    """
    project_name = serializers.CharField(source='project.name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = ProjectCompanyLink
        fields = [
            'id',
            'project',
            'project_name',
            'company',
            'company_name',
            'role',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'deleted_at',
            'project_name',
            'company_name',
        ]

    def validate_role(self, value):
        """역할 검증"""
        valid_roles = [choice[0] for choice in ProjectCompanyLink.ROLE_CHOICES]
        if value not in valid_roles:
            raise serializers.ValidationError(
                f"역할은 {valid_roles} 중 하나여야 합니다."
            )
        return value

    def validate(self, data):
        """전체 필드 검증"""
        project = data.get('project') or (self.instance.project if self.instance else None)
        role = data.get('role') or (self.instance.role if self.instance else None)

        # 같은 프로젝트에 같은 역할이 이미 존재하는지 확인
        if project and role:
            existing = ProjectCompanyLink.objects.filter(
                project=project,
                role=role,
                deleted_at__isnull=True
            )
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError({
                    'role': f'이 프로젝트에 {role} 역할이 이미 존재합니다.'
                })

        return data


class ProjectAssigneeModelSerializer(serializers.ModelSerializer):
    """
    ProjectAssignee 모델의 Serializer

    프로젝트 담당자 정보를 직렬화/역직렬화합니다.
    """
    project_name = serializers.CharField(source='project.name', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = ProjectAssignee
        fields = [
            'id',
            'project',
            'project_name',
            'user',
            'user_name',
            'user_email',
            'is_primary',
            'created_at',
            'deleted_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'deleted_at',
            'project_name',
            'user_name',
            'user_email',
        ]

    def validate(self, data):
        """전체 필드 검증"""
        project = data.get('project') or (self.instance.project if self.instance else None)
        user = data.get('user') or (self.instance.user if self.instance else None)
        is_primary = data.get('is_primary', False) if self.instance is None else data.get('is_primary',
                                                                                          self.instance.is_primary)

        # 같은 프로젝트에 같은 사용자가 이미 존재하는지 확인
        if project and user:
            existing = ProjectAssignee.objects.filter(
                project=project,
                user=user,
                deleted_at__isnull=True
            )
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError({
                    'user': '이 프로젝트에 이미 할당된 사용자입니다.'
                })

        # 주요 담당자가 여러 명이면 안됨
        if is_primary and project:
            existing_primary = ProjectAssignee.objects.filter(
                project=project,
                is_primary=True,
                deleted_at__isnull=True
            )
            if self.instance:
                existing_primary = existing_primary.exclude(id=self.instance.id)
            if existing_primary.exists():
                raise serializers.ValidationError({
                    'is_primary': '이 프로젝트에 이미 주요 담당자가 존재합니다.'
                })

        return data