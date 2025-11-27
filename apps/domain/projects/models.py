"""
Projects Domain Models

프로젝트 관련 도메인 모델을 정의합니다.
"""
from django.db import models
from apps.infrastructure.time_stamp.models import TimeStampedSoftDelete
from apps.domain.company.models import Company
from apps.domain.users.models import User


class Project(TimeStampedSoftDelete):
    """
    프로젝트 정보를 관리하는 모델입니다.

    소프트 삭제 기능을 제공하며, 프로젝트 코드는 고유해야 합니다.
    """
    project_code = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="프로젝트 코드"
    )
    name = models.CharField(
        max_length=255,
        help_text="프로젝트명"
    )
    description = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        help_text="프로젝트 설명"
    )
    status = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="프로젝트 상태"
    )
    method = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="공법"
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text="프로젝트 시작일"
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="프로젝트 종료일"
    )

    class Meta:
        db_table = 'projects'
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        indexes = [
            models.Index(fields=['status'], name='idx_project_status'),
            models.Index(fields=['name'], name='idx_project_name'),
            models.Index(fields=['method'], name='idx_method'),
            models.Index(fields=['start_date', 'end_date'], name='idx_project_dates'),
        ]

    def __str__(self):
        return self.name


class ProjectCompanyLink(TimeStampedSoftDelete):
    """
    프로젝트와 회사의 연결 정보를 관리하는 모델입니다.

    하나의 프로젝트에 여러 회사가 연결될 수 있으며,
    각 회사는 프로젝트 내에서 특정 역할(CLIENT, DESIGN, CONSTRUCTION)을 가집니다.
    """
    ROLE_CHOICES = [
        ('CLIENT', '클라이언트'),
        ('DESIGN', '디자인'),
        ('CONSTRUCTION', '시공'),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='company_links',
        help_text="프로젝트"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='project_links',
        help_text="회사"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        help_text="프로젝트 내 역할"
    )

    class Meta:
        db_table = 'project_company_links'
        verbose_name = 'Project Company Link'
        verbose_name_plural = 'Project Company Links'
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'role'],
                name='uk_project_role'
            ),
            models.CheckConstraint(
                check=models.Q(role__in=['CLIENT', 'DESIGN', 'CONSTRUCTION']),
                name='ck_pcl_role'
            ),
        ]

    def __str__(self):
        return f"{self.project.name} - {self.company.name} ({self.role})"


class ProjectAssignee(TimeStampedSoftDelete):
    """
    프로젝트 담당자 정보를 관리하는 모델입니다.

    하나의 프로젝트에 여러 사용자가 할당될 수 있으며,
    각 사용자는 프로젝트 내에서 주요 담당자로 지정될 수 있습니다.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='assignees',
        help_text="프로젝트"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_projects',
        help_text="담당자"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="주요 담당자 여부"
    )

    class Meta:
        db_table = 'project_assignees'
        verbose_name = 'Project Assignee'
        verbose_name_plural = 'Project Assignees'
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'user'],
                name='uk_project_user'
            ),
        ]
        indexes = [
            models.Index(fields=['user'], name='idx_project_assignee_user'),
            models.Index(fields=['project'], name='idx_project_assignee_project'),
        ]

    def __str__(self):
        primary_text = " (주요)" if self.is_primary else ""
        return f"{self.project.name} - {self.user.name}{primary_text}"