"""
Sales Domain Models

영업(Sales) 관련 도메인 모델을 정의합니다.
"""
from django.db import models
from apps.infrastructure.time_stamp.models import TimeStampedSoftDelete
from apps.domain.projects.models import Project
from apps.domain.users.models import User


class ProjectSales(TimeStampedSoftDelete):
    """
    프로젝트 영업 정보를 관리하는 모델입니다.

    프로젝트의 영업 관련 정보를 관리합니다.
    소프트 삭제 기능을 제공합니다.
    """
    # 영업 유형 선택지
    SALES_TYPE_CHOICES = [
        ("METHOD_REVIEW", "공법 심의"),
        ("DESIGN_CHANGE", "설계 변경"),
        ("TECHNICAL_PROPOSAL", "기술 제안"),
        ("PRIVATE_INVESTMENT", "민간 사업 투자"),
        ("DETAILED_DESIGN", "실시설계"),
        ("TURNKEY", "TK"),
        ("DESIGN_APPLICATION", "설계 반영"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='sales',
        help_text="프로젝트"
    )
    sales_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=SALES_TYPE_CHOICES,
        help_text="영업 유형"
    )
    sales_received_date = models.DateField(
        null=True,
        blank=True,
        help_text="영업 접수일"
    )
    estimate_request_date = models.DateField(
        null=True,
        blank=True,
        help_text="견적 요청일"
    )
    estimate_expected_date = models.DateField(
        null=True,
        blank=True,
        help_text="견적 예상일"
    )
    estimate_submit_date = models.DateField(
        null=True,
        blank=True,
        help_text="견적 제출일"
    )
    estimate_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="견적 금액"
    )
    design_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="설계 금액"
    )

    class Meta:
        db_table = 'project_sales'
        verbose_name = 'Project Sales'
        verbose_name_plural = 'Project Sales'
        constraints = [
            models.UniqueConstraint(
                fields=['project'],
                name='uk_sales_project'
            ),
            models.CheckConstraint(
                check=models.Q(sales_type__in=[
                    "METHOD_REVIEW", "DESIGN_CHANGE", "TECHNICAL_PROPOSAL",
                    "PRIVATE_INVESTMENT", "DETAILED_DESIGN", "TURNKEY", "DESIGN_APPLICATION"
                ]),
                name='ck_sales_type_enum',
            ),
        ]
        indexes = [
            models.Index(fields=['project'], name='idx_sales_project'),
            models.Index(fields=['sales_type'], name='idx_sales_type'),
            models.Index(fields=['sales_received_date'], name='idx_sales_received_date'),
        ]

    def __str__(self):
        sales_type_display = self.get_sales_type_display() if self.sales_type else "미지정"
        return f"{self.project.name} - {sales_type_display}"


class SalesAssignee(TimeStampedSoftDelete):
    """
    영업 담당자 정보를 관리하는 모델입니다.

    하나의 영업에 여러 사용자가 할당될 수 있으며,
    각 사용자는 영업 내에서 주요 담당자로 지정될 수 있습니다.
    """
    sales = models.ForeignKey(
        ProjectSales,
        on_delete=models.CASCADE,
        related_name='assignees',
        help_text="영업"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_sales',
        help_text="담당자"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="주요 담당자 여부"
    )

    class Meta:
        db_table = 'sales_assignees'
        verbose_name = 'Sales Assignee'
        verbose_name_plural = 'Sales Assignees'
        constraints = [
            models.UniqueConstraint(
                fields=['sales', 'user'],
                name='uk_sales_user'
            ),
        ]
        indexes = [
            models.Index(fields=['user'], name='idx_sales_assignee_user'),
            models.Index(fields=['sales'], name='idx_sales_assignee_sales'),
        ]

    def __str__(self):
        primary_text = " (주요)" if self.is_primary else ""
        return f"{self.sales.project.name} - {self.user.name}{primary_text}"


class SalesHistory(TimeStampedSoftDelete):
    """
    영업 이력 정보를 관리하는 모델입니다.

    영업 진행 과정의 이력을 기록합니다.
    공개/비공개 설정이 가능합니다.
    """
    sales = models.ForeignKey(
        ProjectSales,
        on_delete=models.CASCADE,
        related_name='histories',
        help_text="영업"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_histories',
        help_text="작성자"
    )
    content = models.TextField(
        null=True,
        blank=True,
        help_text="이력 내용"
    )
    is_public = models.BooleanField(
        default=False,
        help_text="공개 여부"
    )

    class Meta:
        db_table = 'sales_histories'
        verbose_name = 'Sales History'
        verbose_name_plural = 'Sales Histories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sales'], name='idx_sales_history_sales'),
            models.Index(fields=['user'], name='idx_sales_history_user'),
            models.Index(fields=['is_public'], name='idx_sales_history_public'),
        ]

    def __str__(self):
        public_text = "공개" if self.is_public else "비공개"
        return f"{self.sales.project.name} - {public_text} ({self.created_at.strftime('%Y-%m-%d') if self.created_at else ''})"