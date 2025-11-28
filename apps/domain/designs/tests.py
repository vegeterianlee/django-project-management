"""
Design Domain Tests

- 모델 테스트: TestCase 사용
- API 테스트: APITestCase 사용
- CRUD: Create, Read(List/Retrieve), Update(전체/부분), Delete 모두 포함
"""
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
import json
from datetime import date
from decimal import Decimal

from apps.domain.designs.models import ProjectDesign, DesignVersion, DesignAssignee, DesignHistory
from apps.domain.projects.models import Project
from apps.domain.users.models import User, Department, Position
from apps.domain.company.models import Company


# ============================================
# 모델 단위 테스트 - TestCase 사용
# ============================================
class ProjectDesignModelTest(TestCase):
    """ProjectDesign 모델 단위 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.project = Project.objects.create(name="테스트 프로젝트")
        cls.design = ProjectDesign.objects.create(
            project=cls.project,
            design_start_date=date(2024, 1, 15),
            design_folder_location="/design/folder/path",
        )

    def test_project_design_creation(self):
        """ProjectDesign 생성 테스트"""
        self.assertIsNotNone(self.design.id)
        self.assertEqual(self.design.project, self.project)
        self.assertEqual(self.design.design_folder_location, "/design/folder/path")

    def test_project_design_soft_delete(self):
        """ProjectDesign 소프트 삭제 테스트"""
        self.design.delete()
        self.design.refresh_from_db()
        self.assertIsNotNone(self.design.deleted_at)
        self.assertTrue(self.design.is_deleted)

    def test_project_design_unique_constraint(self):
        """프로젝트당 하나의 설계만 존재하는지 테스트"""
        with self.assertRaises(Exception):
            ProjectDesign.objects.create(
                project=self.project,
                design_start_date=date(2024, 2, 1),
            )


class DesignVersionModelTest(TestCase):
    """DesignVersion 모델 단위 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.project = Project.objects.create(name="테스트 프로젝트")
        cls.design = ProjectDesign.objects.create(
            project=cls.project,
            design_start_date=date(2024, 1, 15),
        )
        cls.version = DesignVersion.objects.create(
            design=cls.design,
            name="v1.0",
            status="DRAFT",
            submitted_date=date(2024, 2, 1),
            construction_cost=Decimal('5000000.00'),
            pile_quantity=100,
            pile_length=Decimal('20.5'),
            concrete_volume=Decimal('1000.5'),
            pc_length=Decimal('50.0'),
        )

    def test_design_version_creation(self):
        """DesignVersion 생성 테스트"""
        self.assertIsNotNone(self.version.id)
        self.assertEqual(self.version.design, self.design)
        self.assertEqual(self.version.name, "v1.0")
        self.assertEqual(self.version.status, "DRAFT")
        self.assertEqual(self.version.construction_cost, Decimal('5000000.00'))

    def test_design_version_unique_constraint(self):
        """같은 설계에 같은 이름의 버전이 중복되지 않는지 테스트"""
        with self.assertRaises(Exception):
            DesignVersion.objects.create(
                design=self.design,
                name="v1.0",  # 이미 존재하는 이름
                status="APPROVED",
            )


class DesignAssigneeModelTest(TestCase):
    """DesignAssignee 모델 단위 테스트"""

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
        cls.design = ProjectDesign.objects.create(
            project=cls.project,
            design_start_date=date(2024, 1, 15),
        )
        cls.assignee = DesignAssignee.objects.create(
            design=cls.design,
            user=cls.user,
            is_primary=True,
        )

    def test_design_assignee_creation(self):
        """DesignAssignee 생성 테스트"""
        self.assertIsNotNone(self.assignee.id)
        self.assertEqual(self.assignee.design, self.design)
        self.assertEqual(self.assignee.user, self.user)
        self.assertTrue(self.assignee.is_primary)


class DesignHistoryModelTest(TestCase):
    """DesignHistory 모델 단위 테스트"""

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
        cls.design = ProjectDesign.objects.create(
            project=cls.project,
            design_start_date=date(2024, 1, 15),
        )
        cls.history = DesignHistory.objects.create(
            design=cls.design,
            user=cls.user,
            content="테스트 이력 내용",
        )

    def test_design_history_creation(self):
        """DesignHistory 생성 테스트"""
        self.assertIsNotNone(self.history.id)
        self.assertEqual(self.history.design, self.design)
        self.assertEqual(self.history.user, self.user)
        self.assertEqual(self.history.content, "테스트 이력 내용")


# ============================================
# API 통합 테스트 - APITestCase 사용
# ============================================
class ProjectDesignAPITest(APITestCase):
    """ProjectDesign API 통합 테스트 - CRUD 모두 포함"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.project = Project.objects.create(name="테스트 프로젝트")
        cls.design = ProjectDesign.objects.create(
            project=cls.project,
            design_start_date=date(2024, 1, 15),
            design_folder_location="/design/folder/path",
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
    def test_list_project_designs(self):
        """설계 목록 조회 API 테스트 (Read)"""
        response = self.client.get('/api/project-designs/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)

    def test_retrieve_project_design(self):
        """설계 상세 조회 API 테스트 (Read)"""
        response = self.client.get(f'/api/project-designs/{self.design.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.design.id)
        self.assertIn('versions', response_data['data'])
        self.assertIn('versions_count', response_data['data'])
        self.assertIn('assignees', response_data['data'])
        self.assertIn('assignees_count', response_data['data'])
        self.assertIn('histories', response_data['data'])
        self.assertIn('histories_count', response_data['data'])

    # ========== CREATE ==========
    def test_create_project_design(self):
        """설계 생성 API 테스트 (Create)"""
        # ⭐ 새로운 프로젝트 생성 (기존 self.project는 이미 설계가 있음)
        new_project = Project.objects.create(name="새 프로젝트")

        data = {
            "project": new_project.id,
            "design_start_date": "2024-02-01",
            "design_folder_location": "/new/design/folder",
        }
        response = self.client.post('/api/project-designs/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['design_folder_location'], data['design_folder_location'])

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(ProjectDesign.objects.filter(design_folder_location=data['design_folder_location']).exists())

    # ========== UPDATE ==========
    def test_update_project_design(self):
        """설계 전체 수정 API 테스트 (Update - PUT)"""
        data = {
            "project": self.project.id,
            "design_start_date": "2024-03-01",
            "design_folder_location": "/updated/design/folder",
        }
        response = self.client.put(
            f'/api/project-designs/{self.design.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.design.refresh_from_db()
        self.assertEqual(self.design.design_folder_location, "/updated/design/folder")

    def test_partial_update_project_design(self):
        """설계 부분 수정 API 테스트 (Update - PATCH)"""
        data = {
            "design_folder_location": "/patched/design/folder",
        }
        response = self.client.patch(
            f'/api/project-designs/{self.design.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.design.refresh_from_db()
        self.assertEqual(self.design.design_folder_location, "/patched/design/folder")

    # ========== DELETE ==========
    def test_delete_project_design(self):
        """설계 삭제 API 테스트 (Delete - 204 No Content)"""
        design_id = self.design.id
        response = self.client.delete(f'/api/project-designs/{design_id}/')

        # 204 No Content 응답 확인
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')

        # 소프트 삭제 확인
        self.design.refresh_from_db()
        self.assertIsNotNone(self.design.deleted_at)
        self.assertTrue(self.design.is_deleted)

    # ========== 커스텀 액션 ==========
    def test_by_project_action(self):
        """프로젝트별 설계 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/project-designs/by-project/{self.project.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])


class DesignVersionAPITest(APITestCase):
    """DesignVersion API 통합 테스트 - CRUD 모두 포함"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.project = Project.objects.create(name="테스트 프로젝트")
        cls.design = ProjectDesign.objects.create(
            project=cls.project,
            design_start_date=date(2024, 1, 15),
        )
        cls.version = DesignVersion.objects.create(
            design=cls.design,
            name="v1.0",
            status="DRAFT",
            submitted_date=date(2024, 2, 1),
            construction_cost=Decimal('5000000.00'),
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
    def test_list_design_versions(self):
        """설계 버전 목록 조회 API 테스트 (Read)"""
        response = self.client.get('/api/design-versions/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_retrieve_design_version(self):
        """설계 버전 상세 조회 API 테스트 (Read)"""
        response = self.client.get(f'/api/design-versions/{self.version.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.version.id)
        self.assertEqual(response_data['data']['name'], self.version.name)
        self.assertEqual(response_data['data']['status'], self.version.status)

    # ========== CREATE ==========
    def test_create_design_version(self):
        """설계 버전 생성 API 테스트 (Create)"""
        data = {
            "design": self.design.id,
            "name": "v2.0",
            "status": "IN_REVIEW",
            "submitted_date": "2024-03-01",
            "construction_cost": "6000000.00",
            "pile_quantity": 120,
            "pile_length": "25.0",
            "concrete_volume": "1200.0",
            "pc_length": "60.0",
        }
        response = self.client.post('/api/design-versions/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['name'], data['name'])

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(DesignVersion.objects.filter(name=data['name']).exists())

    def test_create_design_version_with_invalid_status(self):
        """설계 버전 생성 API 테스트 - 잘못된 status 값"""
        data = {
            "design": self.design.id,
            "name": "v3.0",
            "status": "INVALID_STATUS",
        }
        response = self.client.post('/api/design-versions/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = self._get_response_data(response)
        self.assertFalse(response_data['success'])

    def test_create_design_version_duplicate_name(self):
        """설계 버전 생성 API 테스트 - 중복된 이름"""
        data = {
            "design": self.design.id,
            "name": "v1.0",  # 이미 존재하는 이름
            "status": "APPROVED",
        }
        response = self.client.post('/api/design-versions/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = self._get_response_data(response)
        self.assertFalse(response_data['success'])

    # ========== UPDATE ==========
    def test_partial_update_design_version(self):
        """설계 버전 부분 수정 API 테스트 (Update - PATCH)"""
        data = {
            "status": "APPROVED",
        }
        response = self.client.patch(
            f'/api/design-versions/{self.version.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.version.refresh_from_db()
        self.assertEqual(self.version.status, "APPROVED")

    # ========== DELETE ==========
    def test_delete_design_version(self):
        """설계 버전 삭제 API 테스트 (Delete - 204 No Content)"""
        version_id = self.version.id
        response = self.client.delete(f'/api/design-versions/{version_id}/')

        # 204 No Content 응답 확인
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 소프트 삭제 확인
        self.version.refresh_from_db()
        self.assertIsNotNone(self.version.deleted_at)
        self.assertTrue(self.version.is_deleted)

    # ========== 커스텀 액션 ==========
    def test_by_design_action(self):
        """설계별 버전 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/design-versions/by-design/{self.design.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_by_status_action(self):
        """상태별 버전 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get('/api/design-versions/by-status/DRAFT/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])


class DesignAssigneeAPITest(APITestCase):
    """DesignAssignee API 통합 테스트 - CRUD 모두 포함"""

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
        cls.design = ProjectDesign.objects.create(
            project=cls.project,
            design_start_date=date(2024, 1, 15),
        )
        cls.assignee = DesignAssignee.objects.create(
            design=cls.design,
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
    def test_list_design_assignees(self):
        """설계 담당자 목록 조회 API 테스트 (Read)"""
        response = self.client.get('/api/design-assignees/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_retrieve_design_assignee(self):
        """설계 담당자 상세 조회 API 테스트 (Read)"""
        response = self.client.get(f'/api/design-assignees/{self.assignee.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.assignee.id)
        self.assertEqual(response_data['data']['is_primary'], True)

    # ========== CREATE ==========
    def test_create_design_assignee(self):
        """설계 담당자 생성 API 테스트 (Create)"""
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
            "design": self.design.id,
            "user": new_user.id,
            "is_primary": False,
        }
        response = self.client.post('/api/design-assignees/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(
            DesignAssignee.objects.filter(
                design=self.design,
                user=new_user
            ).exists()
        )

    def test_create_design_assignee_duplicate(self):
        """설계 담당자 중복 생성 시도 테스트"""
        data = {
            "design": self.design.id,
            "user": self.user.id,  # 이미 존재하는 사용자
            "is_primary": False,
        }
        response = self.client.post('/api/design-assignees/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = self._get_response_data(response)
        self.assertFalse(response_data['success'])

    def test_create_design_assignee_multiple_primary(self):
        """설계 담당자 여러 명을 주요 담당자로 지정 시도 테스트"""
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
            "design": self.design.id,
            "user": new_user.id,
            "is_primary": True,  # 이미 주요 담당자가 있음
        }
        response = self.client.post('/api/design-assignees/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = self._get_response_data(response)
        self.assertFalse(response_data['success'])

    # ========== DELETE ==========
    def test_delete_design_assignee(self):
        """설계 담당자 삭제 API 테스트 (Delete - 204 No Content)"""
        assignee_id = self.assignee.id
        response = self.client.delete(f'/api/design-assignees/{assignee_id}/')

        # 204 No Content 응답 확인
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 소프트 삭제 확인
        self.assignee.refresh_from_db()
        self.assertIsNotNone(self.assignee.deleted_at)
        self.assertTrue(self.assignee.is_deleted)

    # ========== 커스텀 액션 ==========
    def test_by_design_action(self):
        """설계별 담당자 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/design-assignees/by-design/{self.design.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_primary_action(self):
        """설계의 주요 담당자 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/design-assignees/primary/{self.design.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['is_primary'], True)

    def test_by_user_action(self):
        """사용자별 설계 할당 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/design-assignees/by-user/{self.user.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])


class DesignHistoryAPITest(APITestCase):
    """DesignHistory API 통합 테스트 - CRUD 모두 포함"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.company = Company.objects.create(name="테스트 회사", type="CLIENT")
        cls.department = Department.objects.create(name="개발팀")
        cls.position = Position.objects.create(title="시니어 개발자")
        cls.user = User.objects.create(
            user_uid="test_user_006",
            name="테스트 사용자6",
            email="test6@example.com",
            position_id=cls.position.id,
            department_id=cls.department.id,
            company=cls.company,
            password="hashed_password",
        )
        cls.project = Project.objects.create(name="테스트 프로젝트")
        cls.design = ProjectDesign.objects.create(
            project=cls.project,
            design_start_date=date(2024, 1, 15),
        )
        cls.history = DesignHistory.objects.create(
            design=cls.design,
            user=cls.user,
            content="테스트 이력 내용",
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
    def test_list_design_histories(self):
        """설계 이력 목록 조회 API 테스트 (Read)"""
        response = self.client.get('/api/design-histories/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_retrieve_design_history(self):
        """설계 이력 상세 조회 API 테스트 (Read)"""
        response = self.client.get(f'/api/design-histories/{self.history.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.history.id)
        self.assertEqual(response_data['data']['content'], self.history.content)

    # ========== CREATE ==========
    def test_create_design_history(self):
        """설계 이력 생성 API 테스트 (Create)"""
        data = {
            "design": self.design.id,
            "user": self.user.id,
            "content": "새 이력 내용",
        }
        response = self.client.post('/api/design-histories/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(
            DesignHistory.objects.filter(
                design=self.design,
                content=data['content']
            ).exists()
        )

    # ========== UPDATE ==========
    def test_partial_update_design_history(self):
        """설계 이력 부분 수정 API 테스트 (Update - PATCH)"""
        data = {
            "content": "수정된 이력 내용",
        }
        response = self.client.patch(
            f'/api/design-histories/{self.history.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.history.refresh_from_db()
        self.assertEqual(self.history.content, "수정된 이력 내용")

    # ========== DELETE ==========
    def test_delete_design_history(self):
        """설계 이력 삭제 API 테스트 (Delete - 204 No Content)"""
        history_id = self.history.id
        response = self.client.delete(f'/api/design-histories/{history_id}/')

        # 204 No Content 응답 확인
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 소프트 삭제 확인
        self.history.refresh_from_db()
        self.assertIsNotNone(self.history.deleted_at)
        self.assertTrue(self.history.is_deleted)

    # ========== 커스텀 액션 ==========
    def test_by_design_action(self):
        """설계별 이력 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/design-histories/by-design/{self.design.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_by_user_action(self):
        """사용자별 설계 이력 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/design-histories/by-user/{self.user.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])