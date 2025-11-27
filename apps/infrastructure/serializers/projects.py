"""
Projects Serializers

Projects 도메인의 모델을 직렬화/역직렬화하는 Serializer입니다.
"""
from rest_framework import serializers
from apps.domain.projects.models import Project, ProjectCompanyLink, ProjectAssignee
from apps.domain.company.models import Company
from apps.domain.users.models import User


class ProjectModelSerializer(serializers.ModelSerializer):
    """
    Project 모델의 Serializer

    Project 모델의 모든 필드를 직렬화/역직렬화합니다.
    역할별 company_links 분류와 assignees 목록을 포함합니다.
    """
    # 역할별 company_links 분류
    company_links_by_role = serializers.SerializerMethodField()

    # assignees 목록과 개수
    assignees = serializers.SerializerMethodField()
    assignees_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id',
            'project_code',
            'name',
            'description',
            'status',
            'method',
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
            'assignees',
            'assignees_count',
        ]

    def get_company_links_by_role(self, obj):
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
            }

            result[link.role].append(link_data)
            result['count'][link.role] += 1
            result['count']['total'] += 1

        return result

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

    def get_assignees_count(self, obj):
        """
        프로젝트에 할당된 담당자 수를 반환합니다.

        Args:
            obj: Project 인스턴스

        Returns:
            int: 담당자 수
        """
        return obj.assignees.filter(deleted_at__isnull=True).count()

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