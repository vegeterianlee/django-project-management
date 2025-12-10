"""
Company Domain Models

회사 및 연락처 관련 도메인 모델을 정의합니다.
"""
from django.db import models
from apps.infrastructure.time_stamp.models import TimeStampedSoftDelete


class Company(TimeStampedSoftDelete):
    """
    회사 정보를 관리하는 모델입니다.

    소프트 삭제 기능을 제공하며, 회사 타입에 대한 제약 조건을 가집니다.
    """
    COMPANY_TYPES = [
        ("CLIENT", "클라이언트"),
        ("DESIGN", "디자인"),
        ("CONSTRUCTION", "시공"),
    ]

    name = models.CharField(max_length=255, help_text="회사명")
    type = models.CharField(
        max_length=50,
        choices=COMPANY_TYPES,
        help_text="회사 유형"
    )
    address = models.CharField(max_length=255, null=True, blank=True, help_text="주소")
    business_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="사업자등록번호"
    )
    representative = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="대표자명"
    )
    contact_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="연락처"
    )
    email = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="이메일"
    )

    class Meta:
        db_table = 'companies'
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        constraints = [
            models.CheckConstraint(
                check=models.Q(type__in=["CLIENT", "DESIGN", "CONSTRUCTION"]),
                name='ck_company_type_enum',
            ),
        ]
        indexes = [
            models.Index(fields=['type'], name='idx_company_type'),
        ]

    def __str__(self):
        return self.name


class ContactPerson(TimeStampedSoftDelete):
    """
    회사의 연락 담당자 정보를 관리하는 모델입니다.

    회사와 외래키 관계를 가지며, 주요 연락처 여부를 표시할 수 있습니다.
    """
    name = models.CharField(max_length=100, help_text="담당자명")
    email = models.CharField(max_length=255, help_text="이메일")
    mobile = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="휴대폰 번호"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='contact_persons',
        help_text="소속 회사"
    )

    position = models.ForeignKey(
        'users.Position',
        on_delete=models.CASCADE,
        related_name='contact_persons',
        help_text="소속 직급"
    )

    class Meta:
        db_table = 'contact_persons'
        verbose_name = 'Contact Person'
        verbose_name_plural = 'Contact Persons'
        indexes = [
            models.Index(fields=['name'], name='idx_contact_person_name'),
            models.Index(fields=['company'], name='idx_contact_person_company'),
            models.Index(fields=['position'], name='idx_contact_person_position'),

        ]

    def __str__(self):
        return f"{self.name} ({self.company.name})"