"""
Meetings Domain Tests

- 모델 테스트: TestCase 사용
- API 테스트: APITestCase 사용
- CRUD: Create, Read(List/Retrieve), Update(전체/부분), Delete 모두 포함
"""
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
import json
from datetime import date

from apps.domain.meetings.models import Meeting, MeetingAssignee
from apps.domain.projects.models import Project
from apps.domain.users.models import User, Department, Position
from apps.domain.company.models import Company


# ============================================
# 모델 단위 테스트 - TestCase 사용
# ============================================
class MeetingModelTest(TestCase):
    """Meeting 모델 단위 테스트"""

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
        cls.meeting = Meeting.objects.create(
            project=cls.project,
            creator=cls.user,
            phase="DESIGN",
            title="테스트 회의",
            meeting_date=date(2024, 1, 15),
            content="테스트 회의 내용",
            location="회의실 A",
        )

    def test_meeting_creation(self):
        """Meeting 생성 테스트"""
        self.assertIsNotNone(self.meeting.id)
        self.assertEqual(self.meeting.title, "테스트 회의")
        self.assertEqual(self.meeting.phase, "DESIGN")
        self.assertEqual(self.meeting.creator, self.user)

    def test_meeting_soft_delete(self):
        """Meeting 소프트 삭제 테스트"""
        self.meeting.delete()
        self.meeting.refresh_from_db()
        self.assertIsNotNone(self.meeting.deleted_at)
        self.assertTrue(self.meeting.is_deleted)


class MeetingAssigneeModelTest(TestCase):
    """MeetingAssignee 모델 단위 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.company = Company.objects.create(name="테스트 회사", type="CLIENT")
        cls.department = Department.objects.create(name="개발팀")
        cls.position = Position.objects.create(title="시니어 개발자")
        cls.user = User.objects.create(
            user_uid="test_user_002",
            name="테스트 사용자2",
            email="test2@example.com",
            position_id=cls.position.id,
            department_id=cls.department.id,
            company=cls.company,
            password="hashed_password",
        )
        cls.project = Project.objects.create(name="테스트 프로젝트")
        cls.meeting = Meeting.objects.create(
            project=cls.project,
            creator=cls.user,
            phase="DESIGN",
            title="테스트 회의",
            meeting_date=date(2024, 1, 15),
        )
        cls.assignee = MeetingAssignee.objects.create(
            meeting=cls.meeting,
            user=cls.user,
        )

    def test_meeting_assignee_creation(self):
        """MeetingAssignee 생성 테스트"""
        self.assertIsNotNone(self.assignee.id)
        self.assertEqual(self.assignee.meeting, self.meeting)
        self.assertEqual(self.assignee.user, self.user)


# ============================================
# API 통합 테스트 - APITestCase 사용
# ============================================
class MeetingAPITest(APITestCase):
    """Meeting API 통합 테스트 - CRUD 모두 포함"""

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
        cls.meeting = Meeting.objects.create(
            project=cls.project,
            creator=cls.user,
            phase="DESIGN",
            title="테스트 회의",
            meeting_date=date(2024, 1, 15),
            content="테스트 회의 내용",
            location="회의실 A",
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
    def test_list_meetings(self):
        """회의 목록 조회 API 테스트 (Read)"""
        response = self.client.get('/api/meetings/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)

    def test_retrieve_meeting(self):
        """회의 상세 조회 API 테스트 (Read)"""
        response = self.client.get(f'/api/meetings/{self.meeting.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.meeting.id)
        self.assertEqual(response_data['data']['title'], self.meeting.title)
        self.assertIn('assignees', response_data['data'])
        self.assertIn('assignees_count', response_data['data'])

    # ========== CREATE ==========
    def test_create_meeting(self):
        """회의 생성 API 테스트 (Create)"""
        data = {
            "project": self.project.id,
            "creator": self.user.id,
            "phase": "DESIGN",
            "title": "새 회의",
            "meeting_date": "2024-02-01",
            "content": "새 회의 내용",
            "location": "회의실 B",
        }
        response = self.client.post('/api/meetings/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['title'], data['title'])

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(Meeting.objects.filter(title=data['title']).exists())

    # ========== UPDATE ==========
    def test_update_meeting(self):
        """회의 전체 수정 API 테스트 (Update - PUT)"""
        data = {
            "project": self.project.id,
            "creator": self.user.id,
            "phase": "CONSTRUCTION",
            "title": "수정된 회의",
            "meeting_date": "2024-02-15",
            "content": "수정된 회의 내용",
            "location": "회의실 C",
        }
        response = self.client.put(
            f'/api/meetings/{self.meeting.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.title, "수정된 회의")
        self.assertEqual(self.meeting.phase, "CONSTRUCTION")

    def test_partial_update_meeting(self):
        """회의 부분 수정 API 테스트 (Update - PATCH)"""
        data = {
            "title": "부분 수정된 회의",
        }
        response = self.client.patch(
            f'/api/meetings/{self.meeting.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.title, "부분 수정된 회의")

    # ========== DELETE ==========
    def test_delete_meeting(self):
        """회의 삭제 API 테스트 (Delete - 204 No Content)"""
        meeting_id = self.meeting.id
        response = self.client.delete(f'/api/meetings/{meeting_id}/')

        # 204 No Content 응답 확인 (본문 없음)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')

        # 소프트 삭제 확인
        self.meeting.refresh_from_db()
        self.assertIsNotNone(self.meeting.deleted_at)
        self.assertTrue(self.meeting.is_deleted)

    # ========== 커스텀 액션 ==========
    def test_by_project_action(self):
        """프로젝트별 회의 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/meetings/by-project/{self.project.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_by_phase_action(self):
        """Phase별 회의 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get('/api/meetings/by-phase/DESIGN/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_by_creator_action(self):
        """생성자별 회의 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/meetings/by-creator/{self.user.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])


class MeetingAssigneeAPITest(APITestCase):
    """MeetingAssignee API 통합 테스트 - CRUD 모두 포함"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.company = Company.objects.create(name="테스트 회사", type="CLIENT")
        cls.department = Department.objects.create(name="개발팀")
        cls.position = Position.objects.create(title="시니어 개발자")
        cls.user = User.objects.create(
            user_uid="test_user_004",
            name="테스트 사용자4",
            email="test4@example.com",
            position_id=cls.position.id,
            department_id=cls.department.id,
            company=cls.company,
            password="hashed_password",
        )
        cls.project = Project.objects.create(name="테스트 프로젝트")
        cls.meeting = Meeting.objects.create(
            project=cls.project,
            creator=cls.user,
            phase="DESIGN",
            title="테스트 회의",
            meeting_date=date(2024, 1, 15),
        )
        cls.assignee = MeetingAssignee.objects.create(
            meeting=cls.meeting,
            user=cls.user,
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
    def test_list_meeting_assignees(self):
        """회의 참석자 목록 조회 API 테스트 (Read)"""
        response = self.client.get('/api/meeting-assignees/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_retrieve_meeting_assignee(self):
        """회의 참석자 상세 조회 API 테스트 (Read)"""
        response = self.client.get(f'/api/meeting-assignees/{self.assignee.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.assignee.id)

    # ========== CREATE ==========
    def test_create_meeting_assignee(self):
        """회의 참석자 생성 API 테스트 (Create)"""
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

        data = {
            "meeting": self.meeting.id,
            "user": new_user.id,
        }
        response = self.client.post('/api/meeting-assignees/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(
            MeetingAssignee.objects.filter(
                meeting=self.meeting,
                user=new_user
            ).exists()
        )

    def test_create_meeting_assignee_duplicate(self):
        """회의 참석자 중복 생성 시도 테스트"""
        data = {
            "meeting": self.meeting.id,
            "user": self.user.id,  # 이미 존재하는 사용자
        }
        response = self.client.post('/api/meeting-assignees/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = self._get_response_data(response)
        self.assertFalse(response_data['success'])

    # ========== DELETE ==========
    def test_delete_meeting_assignee(self):
        """회의 참석자 삭제 API 테스트 (Delete - 204 No Content)"""
        assignee_id = self.assignee.id
        response = self.client.delete(f'/api/meeting-assignees/{assignee_id}/')

        # 204 No Content 응답 확인
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 소프트 삭제 확인
        self.assignee.refresh_from_db()
        self.assertIsNotNone(self.assignee.deleted_at)
        self.assertTrue(self.assignee.is_deleted)

    # ========== 커스텀 액션 ==========
    def test_by_meeting_action(self):
        """회의별 참석자 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/meeting-assignees/by-meeting/{self.meeting.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_by_user_action(self):
        """사용자별 회의 할당 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/meeting-assignees/by-user/{self.user.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])