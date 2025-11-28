"""
Meeting Repository Implementation

model과 serializer_class만 지정하면 모든 CRUD가 자동으로 동작합니다.
복잡한 쿼리는 커스텀 메서드로 구현합니다.
"""
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, date

from apps.infrastructure.repositories.generic import GenericRepository
from apps.domain.meetings.models import Meeting, MeetingAssignee
from apps.infrastructure.serializers.meetings import (
    MeetingModelSerializer,
    MeetingAssigneeModelSerializer,
)


class MeetingRepository(GenericRepository):
    """
    Meeting Repository

    model과 serializer_class만 지정하면 GenericRepository의 모든 기능을 사용할 수 있습니다.
    """
    model = Meeting
    serializer_class = MeetingModelSerializer

    def get_by_project(self, project_id: int):
        """
        프로젝트별 회의 조회

        Args:
            project_id: 프로젝트 ID

        Returns:
            QuerySet
        """
        return self.filter(Q(project_id=project_id))

    def get_by_phase(self, phase: str):
        """
        Phase별 회의 조회

        Args:
            phase: 프로젝트 Phase

        Returns:
            QuerySet
        """
        return self.filter(Q(phase=phase))

    def get_by_project_and_phase(self, project_id: int, phase: str):
        """
        프로젝트와 Phase별 회의 조회

        Args:
            project_id: 프로젝트 ID
            phase: 프로젝트 Phase

        Returns:
            QuerySet
        """
        return self.filter(Q(project_id=project_id, phase=phase))

    def get_by_creator(self, creator_id: int):
        """
        생성자별 회의 조회

        Args:
            creator_id: 생성자 ID

        Returns:
            QuerySet
        """
        return self.filter(Q(creator_id=creator_id))

    def get_by_date_range(self, start_date: date, end_date: date):
        """
        날짜 범위별 회의 조회

        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            QuerySet
        """
        return self.filter(
            Q(meeting_date__gte=start_date) & Q(meeting_date__lte=end_date)
        )

    def get_by_assignee(self, user_id: int):
        """
        참석자별 회의 조회 (MeetingAssignee를 통한)

        Args:
            user_id: 사용자 ID

        Returns:
            QuerySet
        """
        # MeetingAssignee를 통해 연결된 회의 조회
        meeting_ids = MeetingAssignee.objects.filter(
            user_id=user_id,
            deleted_at__isnull=True
        ).values_list('meeting_id', flat=True)

        return self.filter(Q(id__in=meeting_ids))


class MeetingAssigneeRepository(GenericRepository):
    """
    MeetingAssignee Repository
    """
    model = MeetingAssignee
    serializer_class = MeetingAssigneeModelSerializer

    def get_by_meeting(self, meeting_id: int):
        """회의별 참석자 조회"""
        return self.filter(Q(meeting_id=meeting_id))

    def get_by_user(self, user_id: int):
        """사용자별 회의 할당 조회"""
        return self.filter(Q(user_id=user_id))