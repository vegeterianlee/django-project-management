"""
Tasks Domain Tests

- 모델 테스트: TestCase 사용
- API 테스트: APITestCase 사용
- CRUD: Create, Read(List/Retrieve), Update(전체/부분), Delete 모두 포함
"""
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
import json
from datetime import datetime, date

from apps.domain.tasks.models import Task, TaskAssignee
from apps.domain.projects.models import Project
from apps.domain.users.models import User, Department, Position
from apps.domain.company.models import Company


# ============================================
# 모델 단위 테스트 - TestCase 사용
# ============================================
class TaskModelTest(TestCase):
    """Task 모델 단위 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.project = Project.objects.create(
            name="테스트 프로젝트",
        )
        cls.task = Task.objects.create(
            project=cls.project,
            phase="DESIGN",
            title="테스트 작업",
            description="테스트 작업 설명",
            status="TODO",
            priority="HIGH",
        )

    def test_task_creation(self):
        """Task 생성 테스트"""
        self.assertIsNotNone(self.task.id)
        self.assertEqual(self.task.title, "테스트 작업")
        self.assertEqual(self.task.status, "TODO")
        self.assertEqual(self.task.priority, "HIGH")

    def test_task_soft_delete(self):
        """Task 소프트 삭제 테스트"""
        self.task.delete()
        self.task.refresh_from_db()
        self.assertIsNotNone(self.task.deleted_at)
        self.assertTrue(self.task.is_deleted)


class TaskAssigneeModelTest(TestCase):
    """TaskAssignee 모델 단위 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.company = Company.objects.create(name="테스트 회사", type="CLIENT")
        cls.department = Department.objects.create(name="개발팀")
        cls.position = Position.objects.create(title="시니어 개발자")
        cls.user = User.objects.create(
            user_uid="test_user_001",
            name="테스트 사용자",
            email="test@example.com",
            position_id=cls.position.id,
            department_id=cls.department.id,
            company=cls.company,
            password="hashed_password",
        )
        cls.project = Project.objects.create(name="테스트 프로젝트")
        cls.task = Task.objects.create(
            project=cls.project,
            phase="DESIGN",
            title="테스트 작업",
            status="TODO",
            priority="HIGH",
        )
        cls.assignee = TaskAssignee.objects.create(
            task=cls.task,
            user=cls.user,
            is_primary=True,
        )

    def test_task_assignee_creation(self):
        """TaskAssignee 생성 테스트"""
        self.assertIsNotNone(self.assignee.id)
        self.assertEqual(self.assignee.task, self.task)
        self.assertEqual(self.assignee.user, self.user)
        self.assertTrue(self.assignee.is_primary)


# ============================================
# API 통합 테스트 - APITestCase 사용
# ============================================
class TaskAPITest(APITestCase):
    """Task API 통합 테스트 - CRUD 모두 포함"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.project = Project.objects.create(name="테스트 프로젝트")
        cls.task = Task.objects.create(
            project=cls.project,
            phase="DESIGN",
            title="테스트 작업",
            description="테스트 작업 설명",
            category="건축설계",  # DESIGN phase이므로 category 필수
            status="TODO",
            priority="HIGH",
        )

    def _get_response_data(self, response):
        """BaseJsonResponse에서 데이터를 추출하는 헬퍼 메서드"""
        if response.status_code == status.HTTP_204_NO_CONTENT:
            return None
        if hasattr(response, 'content') and response.content:
            try:
                return json.loads(response.content.decode('utf-8'))
            except json.JSONDecodeError:
                return {}
        return response.data

    # ========== READ ==========
    def test_list_tasks(self):
        """작업 목록 조회 API 테스트 (Read)"""
        response = self.client.get('/api/tasks/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)

    def test_list_tasks_with_pagination(self):
        """작업 목록 조회 API 테스트 - 페이지네이션"""
        response = self.client.get('/api/tasks/', {'page': 1, 'page_size': 10})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_retrieve_task(self):
        """작업 상세 조회 API 테스트 (Read)"""
        response = self.client.get(f'/api/tasks/{self.task.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.task.id)
        self.assertEqual(response_data['data']['title'], self.task.title)
        self.assertIn('assignees', response_data['data'])
        self.assertIn('assignees_count', response_data['data'])

    # ========== CREATE ==========
    def test_create_task(self):
        """작업 생성 API 테스트 (Create)"""
        data = {
            "project": self.project.id,
            "phase": "DESIGN",
            "title": "새 작업",
            "description": "새 작업 설명",
            "category": "건축설계",  # DESIGN phase이므로 category 필수
            "status": "TODO",
            "priority": "MEDIUM",
        }
        response = self.client.post('/api/tasks/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['title'], data['title'])

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(Task.objects.filter(title=data['title']).exists())

    def test_create_task_without_category_for_design(self):
        """작업 생성 API 테스트 - DESIGN phase인데 category 없음 (실패해야 함)"""
        data = {
            "project": self.project.id,
            "phase": "DESIGN",
            "title": "카테고리 없는 작업",
            "status": "TODO",
            "priority": "MEDIUM",
            # category 없음
        }
        response = self.client.post('/api/tasks/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = self._get_response_data(response)
        self.assertFalse(response_data['success'])
        self.assertIn('category', response_data.get('data', {}))

    def test_create_task_with_category_for_non_design(self):
        """작업 생성 API 테스트 - DESIGN이 아닌 phase는 category 선택적"""
        data = {
            "project": self.project.id,
            "phase": "SALES",
            "title": "영업 작업",
            "status": "TODO",
            "priority": "MEDIUM",
            # category 없어도 됨
        }
        response = self.client.post('/api/tasks/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_create_task_with_invalid_status(self):
        """작업 생성 API 테스트 - 잘못된 status 값"""
        data = {
            "project": self.project.id,
            "phase": "DESIGN",
            "title": "잘못된 상태 작업",
            "category": "건축설계",
            "status": "INVALID_STATUS",
            "priority": "MEDIUM",
        }
        response = self.client.post('/api/tasks/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = self._get_response_data(response)
        self.assertFalse(response_data['success'])

    def test_create_task_with_invalid_priority(self):
        """작업 생성 API 테스트 - 잘못된 priority 값"""
        data = {
            "project": self.project.id,
            "phase": "DESIGN",
            "title": "잘못된 우선순위 작업",
            "category": "건축설계",
            "status": "TODO",
            "priority": "INVALID_PRIORITY",
        }
        response = self.client.post('/api/tasks/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = self._get_response_data(response)
        self.assertFalse(response_data['success'])

    # ========== UPDATE ==========
    def test_update_task(self):
        """작업 전체 수정 API 테스트 (Update - PUT)"""
        data = {
            "project": self.project.id,
            "phase": "DESIGN",
            "title": "수정된 작업",
            "description": "수정된 작업 설명",
            "category": "구조설계",
            "status": "DOING",
            "priority": "LOW",
        }
        response = self.client.put(
            f'/api/tasks/{self.task.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "수정된 작업")
        self.assertEqual(self.task.status, "DOING")
        self.assertEqual(self.task.priority, "LOW")

    def test_partial_update_task(self):
        """작업 부분 수정 API 테스트 (Update - PATCH)"""
        data = {
            "status": "DONE",
        }
        response = self.client.patch(
            f'/api/tasks/{self.task.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "DONE")

    def test_partial_update_task_change_phase_to_design_without_category(self):
        """작업 부분 수정 API 테스트 - phase를 DESIGN으로 변경했는데 category 없음 (실패해야 함)"""
        # 먼저 SALES phase로 작업 생성
        task = Task.objects.create(
            project=self.project,
            phase="SALES",
            title="영업 작업",
            status="TODO",
            priority="MEDIUM",
        )

        # phase를 DESIGN으로 변경하지만 category 없음
        data = {
            "phase": "DESIGN",
        }
        response = self.client.patch(
            f'/api/tasks/{task.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = self._get_response_data(response)
        self.assertFalse(response_data['success'])
        self.assertIn('category', response_data.get('data', {}))

    # ========== DELETE ==========
    def test_delete_task(self):
        """작업 삭제 API 테스트 (Delete - 204 No Content)"""
        task_id = self.task.id
        response = self.client.delete(f'/api/tasks/{task_id}/')

        # 204 No Content 응답 확인 (본문 없음)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')  # 빈 본문 확인

        # 소프트 삭제 확인
        self.task.refresh_from_db()
        self.assertIsNotNone(self.task.deleted_at)
        self.assertTrue(self.task.is_deleted)

    # ========== 커스텀 액션 ==========
    def test_by_project_action(self):
        """프로젝트별 작업 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/tasks/by-project/{self.project.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)

    def test_by_phase_action(self):
        """Phase별 작업 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get('/api/tasks/by-phase/DESIGN/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_by_project_phase_action(self):
        """프로젝트와 Phase별 작업 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/tasks/by-project-phase/{self.project.id}/DESIGN/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_by_status_action(self):
        """상태별 작업 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get('/api/tasks/by-status/TODO/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_by_priority_action(self):
        """우선순위별 작업 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get('/api/tasks/by-priority/HIGH/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_by_assignee_action(self):
        """담당자별 작업 조회 API 테스트 (커스텀 액션)"""
        # 사용자 생성 및 할당
        company = Company.objects.create(name="테스트 회사", type="CLIENT")
        department = Department.objects.create(name="개발팀")
        position = Position.objects.create(title="시니어 개발자")
        user = User.objects.create(
            user_uid="test_user_002",
            name="테스트 사용자2",
            email="test2@example.com",
            position_id=position.id,
            department_id=department.id,
            company=company,
            password="hashed_password",
        )
        TaskAssignee.objects.create(
            task=self.task,
            user=user,
            is_primary=False,
        )

        response = self.client.get(f'/api/tasks/by-assignee/{user.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_active_action(self):
        """진행 중인 작업 조회 API 테스트 (커스텀 액션)"""
        # 현재 날짜 범위 내 작업 생성
        from django.utils import timezone
        today = timezone.now().date()
        task = Task.objects.create(
            project=self.project,
            phase="DESIGN",
            title="진행 중 작업",
            category="건축설계",
            status="DOING",
            priority="MEDIUM",
            start_date=timezone.make_aware(datetime.combine(today, datetime.min.time())),
            end_date=timezone.make_aware(datetime.combine(today, datetime.max.time())),
        )

        response = self.client.get('/api/tasks/active/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])


# ============================================
# TaskAssignee API 테스트
# ============================================
class TaskAssigneeAPITest(APITestCase):
    """TaskAssignee API 통합 테스트 - CRUD 모두 포함"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.company = Company.objects.create(name="테스트 회사", type="CLIENT")
        cls.department = Department.objects.create(name="개발팀")
        cls.position = Position.objects.create(title="시니어 개발자")
        cls.user = User.objects.create(
            user_uid="test_user_003",
            name="테스트 사용자3",
            email="test3@example.com",
            position_id=cls.position.id,
            department_id=cls.department.id,
            company=cls.company,
            password="hashed_password",
        )
        cls.project = Project.objects.create(name="테스트 프로젝트")
        cls.task = Task.objects.create(
            project=cls.project,
            phase="DESIGN",
            title="테스트 작업",
            category="건축설계",
            status="TODO",
            priority="HIGH",
        )
        cls.assignee = TaskAssignee.objects.create(
            task=cls.task,
            user=cls.user,
            is_primary=True,
        )

    def _get_response_data(self, response):
        """BaseJsonResponse에서 데이터를 추출하는 헬퍼 메서드"""
        if response.status_code == status.HTTP_204_NO_CONTENT:
            return None
        if hasattr(response, 'content') and response.content:
            try:
                return json.loads(response.content.decode('utf-8'))
            except json.JSONDecodeError:
                return {}
        return response.data

    # ========== READ ==========
    def test_list_task_assignees(self):
        """작업 담당자 목록 조회 API 테스트 (Read)"""
        response = self.client.get('/api/task-assignees/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)

    def test_retrieve_task_assignee(self):
        """작업 담당자 상세 조회 API 테스트 (Read)"""
        response = self.client.get(f'/api/task-assignees/{self.assignee.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.assignee.id)
        self.assertEqual(response_data['data']['user'], self.user.id)
        self.assertEqual(response_data['data']['is_primary'], True)

    # ========== CREATE ==========
    def test_create_task_assignee(self):
        """작업 담당자 생성 API 테스트 (Create)"""
        # 새 사용자 생성
        new_user = User.objects.create(
            user_uid="test_user_004",
            name="테스트 사용자4",
            email="test4@example.com",
            position_id=self.position.id,
            department_id=self.department.id,
            company=self.company,
            password="hashed_password",
        )

        data = {
            "task": self.task.id,
            "user": new_user.id,
            "is_primary": False,
        }
        response = self.client.post('/api/task-assignees/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['user'], new_user.id)

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(
            TaskAssignee.objects.filter(
                task=self.task,
                user=new_user
            ).exists()
        )

    def test_create_task_assignee_duplicate(self):
        """작업 담당자 중복 생성 시도 테스트"""
        data = {
            "task": self.task.id,
            "user": self.user.id,  # 이미 존재하는 사용자
            "is_primary": False,
        }
        response = self.client.post('/api/task-assignees/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = self._get_response_data(response)
        self.assertFalse(response_data['success'])

    def test_create_task_assignee_multiple_primary(self):
        """작업 담당자 여러 명을 주요 담당자로 지정 시도 테스트"""
        # 새 사용자 생성
        new_user = User.objects.create(
            user_uid="test_user_005",
            name="테스트 사용자5",
            email="test5@example.com",
            position_id=self.position.id,
            department_id=self.department.id,
            company=self.company,
            password="hashed_password",
        )

        # 이미 주요 담당자가 있는데 또 주요 담당자로 지정 시도
        data = {
            "task": self.task.id,
            "user": new_user.id,
            "is_primary": True,  # 이미 주요 담당자가 있음
        }
        response = self.client.post('/api/task-assignees/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = self._get_response_data(response)
        self.assertFalse(response_data['success'])

    # ========== UPDATE ==========
    def test_update_task_assignee(self):
        """작업 담당자 전체 수정 API 테스트 (Update - PUT)"""
        data = {
            "task": self.task.id,
            "user": self.user.id,
            "is_primary": False,  # 주요 담당자 해제
        }
        response = self.client.put(
            f'/api/task-assignees/{self.assignee.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.assignee.refresh_from_db()
        self.assertEqual(self.assignee.is_primary, False)

    def test_partial_update_task_assignee(self):
        """작업 담당자 부분 수정 API 테스트 (Update - PATCH)"""
        data = {
            "is_primary": False,
        }
        response = self.client.patch(
            f'/api/task-assignees/{self.assignee.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.assignee.refresh_from_db()
        self.assertEqual(self.assignee.is_primary, False)

    # ========== DELETE ==========
    def test_delete_task_assignee(self):
        """작업 담당자 삭제 API 테스트 (Delete - 204 No Content)"""
        assignee_id = self.assignee.id
        response = self.client.delete(f'/api/task-assignees/{assignee_id}/')

        # 204 No Content 응답 확인 (본문 없음)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')  # 빈 본문 확인

        # 소프트 삭제 확인
        self.assignee.refresh_from_db()
        self.assertIsNotNone(self.assignee.deleted_at)
        self.assertTrue(self.assignee.is_deleted)

    # ========== 커스텀 액션 ==========
    def test_by_task_action(self):
        """작업별 담당자 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/task-assignees/by-task/{self.task.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)

    def test_primary_action(self):
        """작업의 주요 담당자 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/task-assignees/primary/{self.task.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['is_primary'], True)

    def test_by_user_action(self):
        """사용자별 작업 할당 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/task-assignees/by-users/{self.user.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)