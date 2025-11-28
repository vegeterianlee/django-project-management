"""
Design Domain Models

설계(Design) 관련 도메인 모델을 정의합니다.
"""
from django.db import models
from apps.infrastructure.time_stamp.models import TimeStampedSoftDelete
from apps.domain.projects.models import Project
from apps.domain.users.models import User


class ProjectDesign(TimeStampedSoftDelete):
    """
    프로젝트 설계 정보를 관리하는 모델입니다.

    프로젝트의 설계 관련 정보를 관리합니다.
    소프트 삭제 기능을 제공합니다.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='designs',
        help_text="프로젝트"
    )
    design_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="설계 시작일"
    )
    design_folder_location = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="설계 폴더 위치"
    )

    class Meta:
        db_table = 'project_designs'
        verbose_name = 'Project Design'
        verbose_name_plural = 'Project Designs'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['project'],
                name='uk_design_project'
            ),
        ]
        indexes = [
            models.Index(fields=['project'], name='idx_design_project'),
            models.Index(fields=['design_start_date'], name='idx_design_start_date'),
        ]

    def __str__(self):
        return f"{self.project.name} - 설계"


class DesignVersion(TimeStampedSoftDelete):
    """
    설계 버전 정보를 관리하는 모델입니다.

    하나의 프로젝트 설계에 여러 버전이 존재할 수 있습니다.
    소프트 삭제 기능을 제공합니다.
    """
    # 설계 버전 상태 선택지
    STATUS_CHOICES = [
        ("DRAFT", "초안"),
        ("IN_REVIEW", "검토 중"),
        ("APPROVED", "승인됨"),
        ("REJECTED", "반려됨"),
        ("SUBMITTED", "제출됨"),
    ]

    design = models.ForeignKey(
        ProjectDesign,
        on_delete=models.CASCADE,
        related_name='versions',
        help_text="설계"
    )
    name = models.CharField(
        max_length=100,
        help_text="버전명"
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        help_text="상태"
    )
    submitted_date = models.DateField(
        null=True,
        blank=True,
        help_text="제출일"
    )
    construction_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="공사비"
    )
    pile_quantity = models.IntegerField(
        null=True,
        blank=True,
        help_text="말뚝 수량"
    )
    pile_length = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="말뚝 길이"
    )
    concrete_volume = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="콘크리트 체적"
    )
    pc_length = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="PC 길이"
    )

    class Meta:
        db_table = 'design_versions'
        verbose_name = 'Design Version'
        verbose_name_plural = 'Design Versions'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['design', 'name'],
                name='uk_design_name'
            ),
            models.CheckConstraint(
                check=models.Q(status__in=[
                    "DRAFT", "IN_REVIEW", "APPROVED", "REJECTED", "SUBMITTED"
                ]),
                name='ck_design_version_status_enum',
            ),
        ]
        indexes = [
            models.Index(fields=['design'], name='idx_version_design'),
            models.Index(fields=['status'], name='idx_version_status'),
            models.Index(fields=['submitted_date'], name='idx_version_submitted_date'),
        ]

    def __str__(self):
        return f"{self.design.project.name} - {self.name} ({self.get_status_display()})"


class DesignAssignee(TimeStampedSoftDelete):
    """
    설계 담당자 정보를 관리하는 모델입니다.

    하나의 설계에 여러 사용자가 할당될 수 있으며,
    각 사용자는 설계 내에서 주요 담당자로 지정될 수 있습니다.
    """
    design = models.ForeignKey(
        ProjectDesign,
        on_delete=models.CASCADE,
        related_name='assignees',
        help_text="설계"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_designs',
        help_text="담당자"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="주요 담당자 여부"
    )

    class Meta:
        db_table = 'design_assignees'
        verbose_name = 'Design Assignee'
        verbose_name_plural = 'Design Assignees'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['design', 'user'],
                name='uk_design_user'
            ),
        ]
        indexes = [
            models.Index(fields=['user'], name='idx_design_assignee_user'),
            models.Index(fields=['design'], name='idx_design_assignee_design'),
        ]

    def __str__(self):
        primary_text = " (주요)" if self.is_primary else ""
        return f"{self.design.project.name} - {self.user.name}{primary_text}"


class DesignHistory(TimeStampedSoftDelete):
    """
    설계 이력 정보를 관리하는 모델입니다.

    설계 진행 과정의 이력을 기록합니다.
    """
    design = models.ForeignKey(
        ProjectDesign,
        on_delete=models.CASCADE,
        related_name='histories',
        help_text="설계"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='design_histories',
        help_text="작성자"
    )
    content = models.TextField(
        null=True,
        blank=True,
        help_text="이력 내용"
    )

    class Meta:
        db_table = 'design_histories'
        verbose_name = 'Design History'
        verbose_name_plural = 'Design Histories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['design'], name='idx_history_design'),
            models.Index(fields=['user'], name='idx_history_user'),
        ]

    def __str__(self):
        return f"{self.design.project.name} - 이력 ({self.created_at.strftime('%Y-%m-%d') if self.created_at else ''})"