"""
Users Domain Models

사용자, 부서, 직급, 권한 관련 도메인 모델을 정의합니다.
"""
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.domain.company.models import Company
from apps.domain.enums.departments import ORGANIZATION_TYPE_CHOICES
from apps.infrastructure.time_stamp.models import TimeStampedSoftDelete


class Department(models.Model):
    """
    부서 정보를 관리하는 모델입니다.

    계층적 구조를 지원하며, 각 부서는 부서장을 가질 수 있습니다.
    계층 구조:
    - BUSINESS_UNIT (사업 수행팀) - 최상위
      ├── HQ (본사 조직) - 하위
      └── FIELD (현장 조직) - 하위
    """

    organization_type = models.CharField(
        max_length=20,
        choices=ORGANIZATION_TYPE_CHOICES,
        help_text="조직 타입"
    )

    parent_department = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='sub_departments',
        help_text="상위 부서 (None이면 최상위 부서)"
    )

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="부서명"
    )
    description = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="부서 설명"
    )

    class Meta:
        db_table = 'departments'
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        indexes = [
            models.Index(fields=['name'], name='idx_department_name'),
            models.Index(fields=['parent_department'], name='idx_department_parent'),
            models.Index(fields=['organization_type'], name='idx_department_org_type'),
        ]

    def __str__(self):
        return self.name

    def get_top_level_department(self):
        """
        해당 부서의 최상위 부서를 반환합니다.

        Returns:
            Department: 최상위 부서 (자기 자신이 최상위면 자기 자신을 반환)
        """
        current = self
        while current.parent_department is not None:
            current = current.parent_department
        return current

    def is_sub_department_of(self, department):
        """
        하위 부서인지 여부를 반환합니다.

        Returns:
            bool: 하위 부서 여부
        """
        current = self.parent_department
        while current:
            if current == department:
                return True
            current = current.parent_department
        return False

    def get_manager(self):
        """
        현재 활성 manager를 반환합니다.

        Returns:
            User: 부서장
        """
        manager = self.managers.filter(deleted_at__isnull=True).first()
        return manager.user if manager else None

    def set_manager(self, user):
        """
        현재 부서장을 변경합니다.

        Args:
            user: User 인스턴스
        """

        # 기존 manager 소프트 삭제
        DepartmentManager.objects.filter(
            department=self,
            deleted_at__isnull=True
        ).update(deleted_at=timezone.now())

        # 새 manager 생성
        DepartmentManager.objects.create(
            department=self,
            user=user
        )

    def is_business_unit(self):
        """
        사업부 부서인지 여부를 반환합니다.
        """
        return self.organization_type == 'BUSINESS_UNIT'


class Position(models.Model):
    """
    직급 정보를 관리하는 모델입니다.

    계층 레벨과 임원 여부를 관리하며, 직급명은 고유해야 합니다.
    """
    title = models.CharField(
        max_length=100,
        unique=True,
        help_text="직급명"
    )
    description = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="직급 설명"
    )
    hierarchy_level = models.IntegerField(
        default=0,
        help_text="직급 계층 레벨 (높을수록 높은 직급)"
    )
    is_executive = models.BooleanField(
        default=False,
        help_text="임원 여부 (Super admin이 설정)"
    )

    class Meta:
        db_table = 'positions'
        verbose_name = 'Position'
        verbose_name_plural = 'Positions'
        indexes = [
            models.Index(fields=['hierarchy_level'], name='idx_position_hierarchy'),
            models.Index(fields=['is_executive'], name='idx_position_executive'),
        ]

    def __str__(self):
        return self.title


class User(TimeStampedSoftDelete, AbstractBaseUser, PermissionsMixin):
    """
    사용자 정보를 관리하는 모델입니다.

    AbstractBaseUser를 상속받아 Django 인증 시스템과 통합됩니다.
    소프트 삭제 기능을 제공하며, 회사, 부서, 직급과의 관계를 가집니다.
    계정 잠금 기능도 포함합니다.
    """
    USERNAME_FIELD = 'user_uid'
    REQUIRED_FIELDS = ['email', 'name']

    user_uid = models.CharField(
        max_length=100,
        unique=True,
        help_text="사용자 고유 ID"
    )
    name = models.CharField(max_length=100, help_text="사용자명")
    email = models.CharField(max_length=255, help_text="이메일")
    position_id = models.IntegerField(help_text="직급 ID")
    department_id = models.IntegerField(help_text="부서 ID")
    company = models.ForeignKey(
        Company,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='users',
        help_text="소속 회사"
    )
    profile_url = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="프로필 이미지 URL"
    )
    color = models.CharField(
        max_length=7,
        null=True,
        blank=True,
        help_text="사용자 색상 코드 (HEX)"
    )
    #password = models.CharField(max_length=255, help_text="비밀번호 (해시)")
    account_locked = models.BooleanField(
        default=False,
        help_text="계정 잠금 여부"
    )
    login_attempts = models.IntegerField(
        default=0,
        help_text="로그인 시도 횟수"
    )
    lock_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="계정 잠금 시간"
    )
    joined_at = models.DateField(
        help_text="입사일"
    )

    sign_url = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="개인 sign file url"
    )

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email'], name='idx_user_email'),
            models.Index(fields=['company'], name='idx_user_company'),
            models.Index(fields=['department_id'], name='idx_user_department'),
            models.Index(fields=['position_id'], name='idx_user_position'),
            models.Index(fields=['joined_at'], name='idx_user_joined_at'),
            models.Index(fields=['sign_url'], name='idx_user_sign_url'),
        ]


    def __str__(self):
        return f"{self.name} ({self.user_uid})"

    def get_username(self):
        """사용자명 반환 (USERNAME_FIELD 값)"""
        return getattr(self, self.USERNAME_FIELD)

class UserPermission(models.Model):
    """
    사용자 권한 관리 모델입니다.

    Super admin이 특정 사용자의 특정 Phase 권한을 부여/삭제할 수 있도록 합니다.
    사용자, Phase, 권한 타입의 조합이 고유해야 합니다.
    """
    PERMISSION_TYPES = [
        ('READ', '읽기'),
        ('WRITE', '쓰기')
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='permissions',
        help_text="사용자"
    )
    phase = models.CharField(
        max_length=50,
        help_text="Phase (SALES, DESIGN, CONTRACT, CONSTRUCTION)"
    )
    permission_type = models.CharField(
        max_length=20,
        choices=PERMISSION_TYPES,
        help_text="권한 타입"
    )

    class Meta:
        db_table = 'user_permissions'
        verbose_name = 'User Permission'
        verbose_name_plural = 'User Permissions'
        unique_together = [['user', 'phase', 'permission_type']]
        indexes = [
            models.Index(fields=['user'], name='idx_user_permission_user'),
            models.Index(fields=['phase'], name='idx_user_permission_phase'),
        ]

    def __str__(self):
        return f"{self.user.name} - {self.phase} ({self.permission_type})"


class DepartmentManager(TimeStampedSoftDelete):
    """
    해당 부서의 manager를 결정하는 모델 입니다
    """

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='managers',
        help_text="부서"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='department_manager',
        help_text="부서장"
    )

    class Meta:
        db_table = 'department_managers'
        verbose_name = 'Department Manager'
        verbose_name_plural = 'Department Managers'
        constraints = [
            models.UniqueConstraint(
                fields=['department'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_active_department_manager'
            )
        ]
        indexes = [
            models.Index(fields=['department'], name='idx_dept_manage_dept'),
            models.Index(fields=['user'], name='idx_dept_manager_user'),
            models.Index(
                fields=['department'],
                name='idx_dept_manager_active'
            ),
        ]

    def __str__(self):
        return f"{self.department.name} - {self.user.name}"


    @classmethod
    def get_active_managers(cls, department):
        """
        해당 부서의 활성화된 부서장을 반환합니다.

        Args:
            department (Department): 부서

        Returns:
            User: 부서장
        """
        return cls.objects.filter(
            department=department,
            deleted_at__isnull=True
        ).first()


class PhaseAccessRule(models.Model):
    """
    Phase별 접근 규칙 관리 모델입니다.

    Super admin이 각 Phase의 접근 규칙을 설정할 수 있도록 합니다.
    필수 부서 목록을 JSON 형식으로 저장합니다.
    """
    PHASE_CHOICES = [
        ('SALES', '영업'),
        ('DESIGN', '디자인'),
        ('CONTRACT', '계약'),
        ('CONSTRUCTION', '시공'),
    ]

    phase = models.CharField(
        max_length=50,
        unique=True,
        choices=PHASE_CHOICES,
        help_text="Phase (SALES, DESIGN, CONTRACT, CONSTRUCTION)"
    )
    required_departments = models.JSONField(
        default=list,
        help_text="필수 부서 목록 (빈 배열이면 부서 제한 없음)"
    )

    class Meta:
        db_table = 'phase_access_rules'
        verbose_name = 'Phase Access Rule'
        verbose_name_plural = 'Phase Access Rules'

    def __str__(self):
        return f"{self.get_phase_display()} Access Rule"