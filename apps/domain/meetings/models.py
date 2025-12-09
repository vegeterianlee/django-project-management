"""
Meetings Domain Models

회의(Meeting) 관련 도메인 모델을 정의합니다.
"""
from django.db import models
from apps.infrastructure.time_stamp.models import TimeStampedSoftDelete
from apps.domain.projects.models import Project
from apps.domain.users.models import User


class Meeting(TimeStampedSoftDelete):
    """
    회의 정보를 관리하는 모델입니다.

    프로젝트의 특정 Phase에서 진행되는 회의를 나타냅니다.
    소프트 삭제 기능을 제공합니다.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='meetings',
        help_text="프로젝트"
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_meetings',
        help_text="회의 생성자"
    )
    phase = models.CharField(
        max_length=50,
        help_text="프로젝트 Phase"
    )
    title = models.CharField(
        max_length=255,
        help_text="회의 제목"
    )
    meeting_date = models.DateField(
        help_text="회의 일자"
    )
    content = models.TextField(
        null=True,
        blank=True,
        help_text="회의 내용"
    )
    location = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="회의 장소"
    )

    class Meta:
        db_table = 'meetings'
        verbose_name = 'Meeting'
        verbose_name_plural = 'Meetings'
        indexes = [
            models.Index(fields=['project'], name='idx_meeting_project'),
            models.Index(fields=['project', 'phase'], name='idx_meeting_project_phase'),
            models.Index(fields=['meeting_date'], name='idx_meeting_date'),
        ]

    def __str__(self):
        return f"{self.title} ({self.meeting_date})"


class MeetingAssignee(TimeStampedSoftDelete):
    """
    회의 참석자 정보를 관리하는 모델입니다.

    하나의 회의에 여러 사용자가 참석할 수 있습니다.
    """
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='assignees',
        help_text="회의"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_meetings',
        help_text="참석자"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="주요 참석자인 지 여부"
    )

    class Meta:
        db_table = 'meeting_assignees'
        verbose_name = 'Meeting Assignee'
        verbose_name_plural = 'Meeting Assignees'
        constraints = [
            models.UniqueConstraint(
                fields=['meeting', 'user'],
                name='uk_meeting_user'
            ),
        ]
        indexes = [
            models.Index(fields=['user'], name='idx_meeting_assignee_user'),
            models.Index(fields=['meeting'], name='idx_meeting_assignee_meeting'),
        ]

    def __str__(self):
        primary_text = " (주요)" if self.is_primary else ""
        return f"{self.meeting.title} - {self.user.name}{primary_text}"