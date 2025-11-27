"""
Tasks Domain Models

작업(Task) 관련 도메인 모델을 정의합니다.
"""
from django.db import models
from apps.infrastructure.time_stamp.models import TimeStampedSoftDelete
from apps.domain.projects.models import Project
from apps.domain.users.models import User


class Task(TimeStampedSoftDelete):
    """
    작업 정보를 관리하는 모델입니다.
    
    프로젝트의 특정 Phase에서 수행되는 작업을 나타냅니다.
    소프트 삭제 기능을 제공합니다.
    """
    # Task 상태 선택지
    STATUS_CHOICES = [
        ("TODO", "할 일"),
        ("DOING", "진행 중"),
        ("DONE", "완료"),
    ]
    
    # Task 우선순위 선택지
    PRIORITY_CHOICES = [
        ("LOW", "낮음"),
        ("MEDIUM", "보통"),
        ("HIGH", "높음"),
    ]
    
    # 프로젝트 Phase 선택지
    PHASE_CHOICES = [
        ("SALES", "영업"),
        ("DESIGN", "디자인"),
        ("CONTRACT", "계약"),
        ("CONSTRUCTION", "시공"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text="프로젝트"
    )
    phase = models.CharField(
        max_length=50,
        choices=PHASE_CHOICES,
        help_text="프로젝트 Phase"
    )
    title = models.CharField(
        max_length=255,
        help_text="작업 제목"
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="작업 설명"
    )
    category = models.CharField(
        null=True,
        blank=True,
        max_length=50,
        help_text="카테고리"
    )
    location = models.CharField(
        null=True,
        blank=True,
        max_length=50,
        help_text="위치"
    )
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="작업 시작일시"
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="작업 종료일시"
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        help_text="작업 상태"
    )
    priority = models.CharField(
        max_length=50,
        choices=PRIORITY_CHOICES,
        help_text="작업 우선순위"
    )

    class Meta:
        db_table = 'tasks'
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=["TODO", "DOING", "DONE"]),
                name='ck_task_status_enum',
            ),
            models.CheckConstraint(
                check=models.Q(priority__in=["LOW", "MEDIUM", "HIGH"]),
                name='ck_task_priority_enum',
            ),
            models.CheckConstraint(
                check=models.Q(phase__in=["SALES", "DESIGN", "CONTRACT", "CONSTRUCTION"]),
                name='ck_task_phase_enum',
            ),
        ]
        indexes = [
            models.Index(fields=['project'], name='idx_task_project'),
            models.Index(fields=['project', 'phase'], name='idx_task_project_phase'),
            models.Index(fields=['status'], name='idx_task_status'),
            models.Index(fields=['priority'], name='idx_task_priority'),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class TaskAssignee(TimeStampedSoftDelete):
    """
    작업 담당자 정보를 관리하는 모델입니다.
    
    하나의 작업에 여러 사용자가 할당될 수 있으며,
    각 사용자는 작업 내에서 주요 담당자로 지정될 수 있습니다.
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='assignees',
        help_text="작업"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='assigned_tasks',
        help_text="담당자"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="주요 담당자 여부"
    )

    class Meta:
        db_table = 'task_assignees'
        verbose_name = 'Task Assignee'
        verbose_name_plural = 'Task Assignees'
        constraints = [
            models.UniqueConstraint(
                fields=['task', 'user'],
                name='uk_task_user'
            ),
        ]
        indexes = [
            models.Index(fields=['user'], name='idx_task_assignee_user'),
            models.Index(fields=['task'], name='idx_task_assignee_task'),
        ]

    def __str__(self):
        primary_text = " (주요)" if self.is_primary else ""
        return f"{self.task.title} - {self.user.name}{primary_text}"
