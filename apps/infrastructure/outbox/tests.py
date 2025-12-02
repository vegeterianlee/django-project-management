"""
Outbox Pattern Tests

Project 모델을 기반으로 하위 연관 모델들이 모두 있다고 가정했을 때
Outbox 패턴이 트리 구조로 연쇄적으로 soft delete를 전파하는지 테스트합니다.
"""
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from decimal import Decimal
from datetime import date

from apps.domain.projects.models import Project, ProjectMethod, ProjectCompanyLink, ProjectAssignee
from apps.domain.tasks.models import Task, TaskAssignee
from apps.domain.designs.models import ProjectDesign, DesignVersion, DesignAssignee, DesignHistory
from apps.domain.sales.models import ProjectSales, SalesAssignee, SalesHistory
from apps.domain.meetings.models import Meeting, MeetingAssignee
from apps.domain.company.models import Company
from apps.domain.users.models import User, Department, Position
from apps.infrastructure.outbox.models import OutboxEvent, OutboxEventStatus
from apps.infrastructure.outbox.tasks import process_soft_delete_propagation


class OutboxSoftDeletePropagationTest(TransactionTestCase):
    """
    Outbox 패턴을 사용한 소프트 삭제 전파 테스트

    TransactionTestCase를 사용하는 이유:
    - Celery 작업이 별도 트랜잭션에서 실행될 수 있기 때문
    - Outbox 이벤트와 실제 삭제가 다른 트랜잭션에서 처리될 수 있기 때문
    """

    def setUp(self):
        """테스트 데이터 준비"""
        # 회사 생성
        self.company = Company.objects.create(
            name="테스트 회사",
            type="CLIENT"
        )

        # 부서 및 직책 생성
        self.department = Department.objects.create(name="개발팀")
        self.position = Position.objects.create(title="시니어 개발자")

        # 사용자 생성 - position_id와 department_id 사용
        self.user1 = User.objects.create(
            user_uid="user_001",
            name="사용자 1",
            email="user1@example.com",
            position_id=self.position.id,  # ✅ position_id 사용
            department_id=self.department.id,  # ✅ department_id 사용
            company=self.company,
            password="hashed_password"
        )

        self.user2 = User.objects.create(
            user_uid="user_002",
            name="사용자 2",
            email="user2@example.com",
            position_id=self.position.id,  # ✅ position_id 사용
            department_id=self.department.id,  # ✅ department_id 사용
            company=self.company,
            password="hashed_password"
        )

        # 프로젝트 생성
        self.project = Project.objects.create(
            project_code="PRJ001",
            name="테스트 프로젝트",
            description="Outbox 패턴 테스트용 프로젝트",
            status="IN_PROGRESS",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )

        # ProjectMethod 생성
        self.project_method1 = ProjectMethod.objects.create(
            project=self.project,
            method="GRB"
        )
        self.project_method2 = ProjectMethod.objects.create(
            project=self.project,
            method="GTCIP"
        )

        # ProjectCompanyLink 생성
        self.company_link = ProjectCompanyLink.objects.create(
            project=self.project,
            company=self.company,
            role="CLIENT"
        )

        # ProjectAssignee 생성
        self.project_assignee1 = ProjectAssignee.objects.create(
            project=self.project,
            user=self.user1,
            is_primary=True
        )
        self.project_assignee2 = ProjectAssignee.objects.create(
            project=self.project,
            user=self.user2,
            is_primary=False
        )

        # Task 생성
        self.task1 = Task.objects.create(
            project=self.project,
            phase="DESIGN",
            title="설계 작업 1",
            description="설계 작업 설명",
            status="TODO",
            priority="HIGH",
            category="STRUCTURE"
        )
        self.task2 = Task.objects.create(
            project=self.project,
            phase="DESIGN",
            title="설계 작업 2",
            status="DOING",
            priority="MEDIUM",
            category="MEP"
        )

        # TaskAssignee 생성
        self.task_assignee1 = TaskAssignee.objects.create(
            task=self.task1,
            user=self.user1,
            is_primary=True
        )
        self.task_assignee2 = TaskAssignee.objects.create(
            task=self.task2,
            user=self.user2,
            is_primary=False
        )

        # ProjectDesign 생성
        self.project_design = ProjectDesign.objects.create(
            project=self.project,
            design_start_date=date(2024, 2, 1),
            design_folder_location="/designs/project1"
        )

        # DesignVersion 생성
        self.design_version1 = DesignVersion.objects.create(
            design=self.project_design,
            name="버전 1.0",
            status="DRAFT",
            submitted_date=date(2024, 2, 15),
            construction_cost=Decimal('1000000.00')
        )
        self.design_version2 = DesignVersion.objects.create(
            design=self.project_design,
            name="버전 2.0",
            status="APPROVED",
            submitted_date=date(2024, 3, 1),
            construction_cost=Decimal('1200000.00')
        )

        # DesignAssignee 생성
        self.design_assignee = DesignAssignee.objects.create(
            design=self.project_design,
            user=self.user1,
            is_primary=True
        )

        # DesignHistory 생성
        self.design_history1 = DesignHistory.objects.create(
            design=self.project_design,
            user=self.user1,
            content="초기 설계 완료"
        )
        self.design_history2 = DesignHistory.objects.create(
            design=self.project_design,
            user=self.user2,
            content="수정 사항 반영"
        )

        # ProjectSales 생성
        self.project_sales = ProjectSales.objects.create(
            project=self.project,
            sales_type="METHOD_REVIEW",
            sales_received_date=date(2024, 1, 15),
            estimate_amount=Decimal('5000000.00'),
            design_amount=Decimal('2000000.00')
        )

        # SalesAssignee 생성
        self.sales_assignee = SalesAssignee.objects.create(
            sales=self.project_sales,
            user=self.user1,
            is_primary=True
        )

        # SalesHistory 생성
        self.sales_history1 = SalesHistory.objects.create(
            sales=self.project_sales,
            user=self.user1,
            content="영업 초기 접촉",
            is_public=True
        )
        self.sales_history2 = SalesHistory.objects.create(
            sales=self.project_sales,
            user=self.user2,
            content="내부 검토",
            is_public=False
        )

        # Meeting 생성
        self.meeting1 = Meeting.objects.create(
            project=self.project,
            creator=self.user1,
            phase="DESIGN",
            title="설계 회의",
            meeting_date=date(2024, 2, 10),
            content="설계 검토 회의",
            location="회의실 A"
        )
        self.meeting2 = Meeting.objects.create(
            project=self.project,
            creator=self.user2,
            phase="DESIGN",
            title="설계 수정 회의",
            meeting_date=date(2024, 2, 20),
            content="설계 수정 사항 논의"
        )

        # MeetingAssignee 생성
        self.meeting_assignee1 = MeetingAssignee.objects.create(
            meeting=self.meeting1,
            user=self.user1
        )
        self.meeting_assignee2 = MeetingAssignee.objects.create(
            meeting=self.meeting2,
            user=self.user2
        )

    def test_outbox_event_created_on_project_delete(self):
        """Project 삭제 시 Outbox 이벤트가 생성되는지 테스트"""
        # 삭제 전 Outbox 이벤트 개수 확인
        initial_count = OutboxEvent.objects.count()

        # Project 삭제
        self.project.delete()

        # Outbox 이벤트가 생성되었는지 확인
        self.assertEqual(OutboxEvent.objects.count(), initial_count + 1)

        # 생성된 이벤트 확인
        outbox_event = OutboxEvent.objects.latest('created_at')
        self.assertEqual(outbox_event.event_type, "soft_delete.propagate")
        self.assertEqual(outbox_event.aggregate_type, "projects.Project")
        self.assertEqual(outbox_event.aggregate_id, str(self.project.id))

        self.assertIn(
            outbox_event.status,
            [OutboxEventStatus.PENDING, OutboxEventStatus.PUBLISHED]
        )

        # 이벤트 데이터 확인
        event_data = outbox_event.event_data
        self.assertEqual(event_data['model_app'], 'projects')
        self.assertEqual(event_data['model_name'], 'Project')
        self.assertEqual(event_data['instance_id'], str(self.project.id))

    def test_soft_delete_propagation_tree_structure(self):
        """
        트리 구조로 연쇄적으로 soft delete가 전파되는지 테스트

        트리 구조:
        Project (depth 0)
        ├─ ProjectMethod (depth 1)
        ├─ ProjectCompanyLink (depth 1)
        ├─ ProjectAssignee (depth 1)
        ├─ Task (depth 1)
        │  └─ TaskAssignee (depth 2)
        ├─ ProjectDesign (depth 1)
        │  ├─ DesignVersion (depth 2)
        │  ├─ DesignAssignee (depth 2)
        │  └─ DesignHistory (depth 2)
        ├─ ProjectSales (depth 1)
        │  ├─ SalesAssignee (depth 2)
        │  └─ SalesHistory (depth 2)
        └─ Meeting (depth 1)
           └─ MeetingAssignee (depth 2)
        """
        # Project 삭제
        self.project.delete()

        # Outbox 이벤트 조회
        outbox_event = OutboxEvent.objects.latest('created_at')

        # Celery 작업 실행 (동기적으로 실행)
        process_soft_delete_propagation(str(outbox_event.id))

        # Outbox 이벤트 상태 확인
        outbox_event.refresh_from_db()
        self.assertEqual(outbox_event.status, OutboxEventStatus.PROCESSED)
        self.assertIsNotNone(outbox_event.processed_at)

        # Project가 삭제되었는지 확인
        self.project.refresh_from_db()
        self.assertIsNotNone(self.project.deleted_at)

        # Depth 1: 직접 하위 모델들 확인
        # ProjectMethod
        self.project_method1.refresh_from_db()
        self.project_method2.refresh_from_db()
        self.assertIsNotNone(self.project_method1.deleted_at)
        self.assertIsNotNone(self.project_method2.deleted_at)

        # ProjectCompanyLink
        self.company_link.refresh_from_db()
        self.assertIsNotNone(self.company_link.deleted_at)

        # ProjectAssignee
        self.project_assignee1.refresh_from_db()
        self.project_assignee2.refresh_from_db()
        self.assertIsNotNone(self.project_assignee1.deleted_at)
        self.assertIsNotNone(self.project_assignee2.deleted_at)

        # Task
        self.task1.refresh_from_db()
        self.task2.refresh_from_db()
        self.assertIsNotNone(self.task1.deleted_at)
        self.assertIsNotNone(self.task2.deleted_at)

        # ProjectDesign
        self.project_design.refresh_from_db()
        self.assertIsNotNone(self.project_design.deleted_at)

        # ProjectSales
        self.project_sales.refresh_from_db()
        self.assertIsNotNone(self.project_sales.deleted_at)

        # Meeting
        self.meeting1.refresh_from_db()
        self.meeting2.refresh_from_db()
        self.assertIsNotNone(self.meeting1.deleted_at)
        self.assertIsNotNone(self.meeting2.deleted_at)

        # Depth 2: 간접 하위 모델들 확인
        # TaskAssignee
        self.task_assignee1.refresh_from_db()
        self.task_assignee2.refresh_from_db()
        self.assertIsNotNone(self.task_assignee1.deleted_at)
        self.assertIsNotNone(self.task_assignee2.deleted_at)

        # DesignVersion
        self.design_version1.refresh_from_db()
        self.design_version2.refresh_from_db()
        self.assertIsNotNone(self.design_version1.deleted_at)
        self.assertIsNotNone(self.design_version2.deleted_at)

        # DesignAssignee
        self.design_assignee.refresh_from_db()
        self.assertIsNotNone(self.design_assignee.deleted_at)

        # DesignHistory
        self.design_history1.refresh_from_db()
        self.design_history2.refresh_from_db()
        self.assertIsNotNone(self.design_history1.deleted_at)
        self.assertIsNotNone(self.design_history2.deleted_at)

        # SalesAssignee
        self.sales_assignee.refresh_from_db()
        self.assertIsNotNone(self.sales_assignee.deleted_at)

        # SalesHistory
        self.sales_history1.refresh_from_db()
        self.sales_history2.refresh_from_db()
        self.assertIsNotNone(self.sales_history1.deleted_at)
        self.assertIsNotNone(self.sales_history2.deleted_at)

        # MeetingAssignee
        self.meeting_assignee1.refresh_from_db()
        self.meeting_assignee2.refresh_from_db()
        self.assertIsNotNone(self.meeting_assignee1.deleted_at)
        self.assertIsNotNone(self.meeting_assignee2.deleted_at)

    def test_soft_delete_propagation_only_deletes_related_models(self):
        """연관되지 않은 모델은 삭제되지 않는지 테스트"""
        # 다른 프로젝트 생성
        other_project = Project.objects.create(
            project_code="PRJ002",
            name="다른 프로젝트",
            status="PLANNING"
        )

        # 다른 프로젝트의 Task 생성
        other_task = Task.objects.create(
            project=other_project,
            phase="DESIGN",
            title="다른 프로젝트 작업",
            status="TODO",
            priority="LOW"
        )

        # 원래 프로젝트 삭제
        self.project.delete()

        # Outbox 이벤트 처리
        outbox_event = OutboxEvent.objects.latest('created_at')
        process_soft_delete_propagation(str(outbox_event.id))

        # 다른 프로젝트와 그 하위 모델들은 삭제되지 않았는지 확인
        other_project.refresh_from_db()
        other_task.refresh_from_db()
        self.assertIsNone(other_project.deleted_at)
        self.assertIsNone(other_task.deleted_at)

    def test_soft_delete_propagation_skips_already_deleted_models(self):
        """이미 삭제된 모델은 다시 삭제하지 않는지 테스트"""
        # Task를 먼저 삭제
        self.task1.delete()
        self.task1.refresh_from_db()
        initial_deleted_at = self.task1.deleted_at

        # Project 삭제
        self.project.delete()

        # Outbox 이벤트 처리
        outbox_event = OutboxEvent.objects.latest('created_at')
        process_soft_delete_propagation(str(outbox_event.id))

        # 이미 삭제된 Task의 deleted_at이 변경되지 않았는지 확인
        self.task1.refresh_from_db()
        self.assertEqual(self.task1.deleted_at, initial_deleted_at)

    def test_soft_delete_propagation_handles_circular_reference(self):
        """순환 참조가 있어도 무한 루프가 발생하지 않는지 테스트"""
        # Project 삭제
        self.project.delete()

        # Outbox 이벤트 처리 (순환 참조가 있어도 안전하게 처리되어야 함)
        outbox_event = OutboxEvent.objects.latest('created_at')

        # 예외 없이 실행되어야 함
        try:
            process_soft_delete_propagation(str(outbox_event.id))
        except Exception as e:
            self.fail(f"순환 참조 처리 중 예외 발생: {e}")

        # Outbox 이벤트가 처리됨으로 표시되었는지 확인
        outbox_event.refresh_from_db()
        self.assertEqual(outbox_event.status, OutboxEventStatus.PROCESSED)

    def test_outbox_event_published_immediately_after_commit(self):
        """트랜잭션 커밋 후 즉시 Outbox 이벤트가 발행되는지 테스트"""
        from django.db import transaction

        with transaction.atomic():
            # 트랜잭션 내에서 Project 삭제
            self.project.delete()

            # 트랜잭션 내에서는 아직 Outbox 이벤트가 발행되지 않았을 수 있음
            outbox_event = OutboxEvent.objects.latest('created_at')
            # published_at은 아직 None일 수 있음 (커밋 전)

        # 트랜잭션 커밋 후
        # transaction.on_commit 콜백이 실행되어야 함
        # 실제로는 Celery 작업이 비동기로 실행되지만,
        # 테스트 환경에서는 CELERY_TASK_ALWAYS_EAGER=True로 설정하여 동기 실행

        # Outbox 이벤트 확인
        outbox_event.refresh_from_db()
        self.assertEqual(outbox_event.status, OutboxEventStatus.PUBLISHED)
        self.assertIsNotNone(outbox_event.published_at)
        self.assertIsNotNone(outbox_event.celery_task_id)

    def test_outbox_event_fallback_republishes_pending_events(self):
        """Fallback 작업이 PENDING 상태의 이벤트를 재발행하는지 테스트"""
        from apps.infrastructure.outbox.tasks import publish_outbox_messages
        from unittest.mock import patch
        import time

        # Project 삭제
        self.project.delete()

        # Outbox 이벤트 조회
        outbox_event = OutboxEvent.objects.latest('created_at')

        # published_at을 None으로 설정하여 발행되지 않은 것처럼 만듦
        outbox_event.published_at = None
        outbox_event.status = OutboxEventStatus.PENDING
        outbox_event.save()

        # created_at을 30초 전으로 설정
        outbox_event.created_at = timezone.now() - timezone.timedelta(seconds=35)
        outbox_event.save()

        # Fallback 작업 실행
        publish_outbox_messages()

        # 이벤트가 재발행되었는지 확인
        outbox_event.refresh_from_db()
        self.assertEqual(outbox_event.status, OutboxEventStatus.PUBLISHED)
        self.assertIsNotNone(outbox_event.published_at)
        self.assertIsNotNone(outbox_event.celery_task_id)