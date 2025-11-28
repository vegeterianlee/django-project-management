"""
Meetings Serializers

Meetings 도메인의 모델을 직렬화/역직렬화하는 Serializer입니다.
"""
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from typing import List, Dict, Any
from apps.domain.meetings.models import Meeting, MeetingAssignee


class MeetingAssigneeModelSerializer(serializers.ModelSerializer):
    """
    MeetingAssignee 모델의 Serializer

    회의 참석자 정보를 직렬화/역직렬화합니다.
    """
    meeting_title = serializers.CharField(source='meeting.title', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = MeetingAssignee
        fields = [
            'id',
            'meeting',
            'meeting_title',
            'user',
            'user_name',
            'user_email',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'deleted_at',
            'meeting_title',
            'user_name',
            'user_email',
        ]

    def validate(self, data):
        """전체 필드 검증"""
        meeting = data.get('meeting') or (self.instance.meeting if self.instance else None)
        user = data.get('user') or (self.instance.user if self.instance else None)

        # 같은 회의에 같은 사용자가 이미 존재하는지 확인
        if meeting and user:
            existing = MeetingAssignee.objects.filter(
                meeting=meeting,
                user=user,
                deleted_at__isnull=True
            )
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError({
                    'user': '이 회의에 이미 참석자로 등록된 사용자입니다.'
                })

        return data


class MeetingModelSerializer(serializers.ModelSerializer):
    """
    Meeting 모델의 Serializer

    회의 정보를 직렬화/역직렬화합니다.
    """
    assignees = serializers.SerializerMethodField()
    assignees_count = serializers.SerializerMethodField()

    class Meta:
        model = Meeting
        fields = [
            'id',
            'project',
            'creator',
            'phase',
            'title',
            'meeting_date',
            'content',
            'location',
            'assignees',
            'assignees_count',
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
    def get_assignees(self, obj: Meeting) -> List[Dict[str, Any]]:
        """
        회의 참석자 목록을 반환합니다.
        """
        assignees = obj.assignees.filter(deleted_at__isnull=True)
        return [
            {
                'id': assignee.id,
                'user_id': assignee.user.id,
                'user_name': assignee.user.name,
                'user_email': assignee.user.email,
            }
            for assignee in assignees
        ]

    @extend_schema_field(serializers.IntegerField())
    def get_assignees_count(self, obj: Meeting) -> int:
        """
        회의 참석자 수를 반환합니다.
        """
        return obj.assignees.filter(deleted_at__isnull=True).count()