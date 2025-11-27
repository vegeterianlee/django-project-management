"""
Tasks Serializers

Tasks 도메인의 모델을 직렬화/역직렬화하는 Serializer입니다.
"""
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from apps.domain.tasks.models import Task, TaskAssignee
from apps.domain.users.models import User


class TaskAssigneeModelSerializer(serializers.ModelSerializer):
    """
    TaskAssignee 모델의 Serializer

    작업 담당자 정보를 직렬화/역직렬화합니다.
    """
    task_title = serializers.CharField(source='task.title', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = TaskAssignee
        fields = [
            'id',
            'task',
            'task_title',
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
            'task_title',
            'user_name',
            'user_email',
        ]

    def validate(self, data):
        """전체 필드 검증"""
        task = data.get('task') or (self.instance.task if self.instance else None)
        user = data.get('user') or (self.instance.user if self.instance else None)
        is_primary = data.get('is_primary', False) if self.instance is None else data.get('is_primary',
                                                                                          self.instance.is_primary)

        # 같은 작업에 같은 사용자가 이미 존재하는지 확인
        if task and user:
            existing = TaskAssignee.objects.filter(
                task=task,
                user=user,
                deleted_at__isnull=True
            )
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError({
                    'user': '이 작업에 이미 할당된 사용자입니다.'
                })

        # 주요 담당자가 여러 명이면 안됨
        if is_primary and task:
            existing_primary = TaskAssignee.objects.filter(
                task=task,
                is_primary=True,
                deleted_at__isnull=True
            )
            if self.instance:
                existing_primary = existing_primary.exclude(id=self.instance.id)
            if existing_primary.exists():
                raise serializers.ValidationError({
                    'is_primary': '이 작업에 이미 주요 담당자가 존재합니다.'
                })

        return data


class TaskModelSerializer(serializers.ModelSerializer):
    """
    Task 모델의 Serializer

    Task 모델의 모든 필드를 직렬화/역직렬화합니다.
    담당자 목록과 개수를 포함합니다.
    """
    # 담당자 목록과 개수
    assignees = serializers.SerializerMethodField()
    assignees_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id',
            'project',
            'phase',
            'title',
            'description',
            'category',
            'location',
            'start_date',
            'end_date',
            'status',
            'priority',
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
            'assignees',
            'assignees_count',
        ]

    @extend_schema_field(
        serializers.ListField(
            child=serializers.DictField()
        )
    )
    def get_assignees(self, obj):
        """
        작업에 할당된 담당자 목록을 반환합니다.

        Args:
            obj: Task 인스턴스

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
    def get_assignees_count(self, obj):
        """
        작업에 할당된 담당자 수를 반환합니다.

        Args:
            obj: Task 인스턴스

        Returns:
            int: 담당자 수
        """
        return obj.assignees.filter(deleted_at__isnull=True).count()

    def validate_status(self, value):
        """상태 검증"""
        valid_statuses = [choice[0] for choice in Task.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"작업 상태는 {valid_statuses} 중 하나여야 합니다."
            )
        return value

    def validate_priority(self, value):
        """우선순위 검증"""
        valid_priorities = [choice[0] for choice in Task.PRIORITY_CHOICES]
        if value not in valid_priorities:
            raise serializers.ValidationError(
                f"작업 우선순위는 {valid_priorities} 중 하나여야 합니다."
            )
        return value

    def validate_phase(self, value):
        """Phase 검증"""
        valid_phases = [choice[0] for choice in Task.PHASE_CHOICES]
        if value not in valid_phases:
            raise serializers.ValidationError(
                f"프로젝트 Phase는 {valid_phases} 중 하나여야 합니다."
            )
        return value


    def validate(self, data):
        """전체 필드 검증"""
        start_date = data.get('start_date') or (self.instance.start_date if self.instance else None)
        end_date = data.get('end_date') or (self.instance.end_date if self.instance else None)

        # 시작일시가 종료일시보다 늦으면 안됨
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'end_date': '종료일시는 시작일시보다 늦어야 합니다.'
            })

        phase = data.get('phase') or (self.instance.phase if self.instance else None)

        # category 값 가져오기 (요청 데이터 또는 기존 인스턴스)
        category = data.get('category') or (self.instance.category if self.instance else None)

        if phase == "DESIGN":
            if not category or category.strip() == "":
                raise serializers.ValidationError({
                    'category': 'DESIGN Phase일 때 category는 필수입니다.'
                })

        return data