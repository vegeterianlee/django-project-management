"""
Sales Domain Tests

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

from apps.domain.sales.models import ProjectSales, SalesAssignee, SalesHistory
from apps.domain.projects.models import Project
from apps.domain.users.models import User, Department, Position
from apps.domain.company.models import Company


# ============================================
# 모델 단위 테스트 - TestCase 사용
# ============================================
class ProjectSalesModelTest(TestCase):
    """ProjectSales 모델 단위 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.project = Project.objects.create(name="테스트 프로젝트")
        cls.sales = ProjectSales.objects.create(
            project=cls.project,
            sales_type="METHOD_REVIEW",
            sales_received_date=date(2024, 1, 15),
            estimate_request_date=date(2024, 1, 20),
            estimate_expected_date=date(2024, 1, 25),
            estimate_submit_date=date(2024, 1, 30),
            estimate_amount=Decimal('1000000.00'),
            design_amount=Decimal('500000.00'),
        )

    def test_project_sales_creation(self):
        """ProjectSales 생성 테스트"""
        self.assertIsNotNone(self.sales.id)
        self.assertEqual(self.sales.sales_type, "METHOD_REVIEW")
        self.assertEqual(self.sales.project, self.project)
        self.assertEqual(self.sales.estimate_amount, Decimal('1000000.00'))

    def test_project_sales_soft_delete(self):
        """ProjectSales 소프트 삭제 테스트"""
        self.sales.delete()
        self.sales.refresh_from_db()
        self.assertIsNotNone(self.sales.deleted_at)
        self.assertTrue(self.sales.is_deleted)

    def test_project_sales_unique_constraint(self):
        """프로젝트당 하나의 영업만 존재하는지 테스트"""
        with self.assertRaises(Exception):
            ProjectSales.objects.create(
                project=self.project,
                sales_type="DESIGN_CHANGE",
            )


class SalesAssigneeModelTest(TestCase):
    """SalesAssignee 모델 단위 테스트"""

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
        cls.sales = ProjectSales.objects.create(
            project=cls.project,
            sales_type="METHOD_REVIEW",
        )
        cls.assignee = SalesAssignee.objects.create(
            sales=cls.sales,
            user=cls.user,
            is_primary=True,
        )

    def test_sales_assignee_creation(self):
        """SalesAssignee 생성 테스트"""
        self.assertIsNotNone(self.assignee.id)
        self.assertEqual(self.assignee.sales, self.sales)
        self.assertEqual(self.assignee.user, self.user)
        self.assertTrue(self.assignee.is_primary)

    def test_sales_assignee_unique_constraint(self):
        """같은 영업에 같은 사용자가 중복되지 않는지 테스트"""
        with self.assertRaises(Exception):
            SalesAssignee.objects.create(
                sales=self.sales,
                user=self.user,
            )


class SalesHistoryModelTest(TestCase):
    """SalesHistory 모델 단위 테스트"""

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
        cls.sales = ProjectSales.objects.create(
            project=cls.project,
            sales_type="METHOD_REVIEW",
        )
        cls.history = SalesHistory.objects.create(
            sales=cls.sales,
            user=cls.user,
            content="테스트 이력 내용",
            is_public=True,
        )

    def test_sales_history_creation(self):
        """SalesHistory 생성 테스트"""
        self.assertIsNotNone(self.history.id)
        self.assertEqual(self.history.sales, self.sales)
        self.assertEqual(self.history.user, self.user)
        self.assertEqual(self.history.content, "테스트 이력 내용")
        self.assertTrue(self.history.is_public)


# ============================================
# API 통합 테스트 - APITestCase 사용
# ============================================
class ProjectSalesAPITest(APITestCase):
    """ProjectSales API 통합 테스트 - CRUD 모두 포함"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.project = Project.objects.create(name="테스트 프로젝트")
        cls.sales = ProjectSales.objects.create(
            project=cls.project,
            sales_type="METHOD_REVIEW",
            sales_received_date=date(2024, 1, 15),
            estimate_amount=Decimal('1000000.00'),
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
    def test_list_project_sales(self):
        """영업 목록 조회 API 테스트 (Read)"""
        response = self.client.get('/api/project-sales/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)

    def test_retrieve_project_sales(self):
        """영업 상세 조회 API 테스트 (Read)"""
        response = self.client.get(f'/api/project-sales/{self.sales.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.sales.id)
        self.assertEqual(response_data['data']['sales_type'], self.sales.sales_type)
        self.assertIn('assignees', response_data['data'])
        self.assertIn('assignees_count', response_data['data'])
        self.assertIn('histories', response_data['data'])
        self.assertIn('histories_count', response_data['data'])

    # ========== CREATE ==========
    def test_create_project_sales(self):
        """영업 생성 API 테스트 (Create)"""
        new_project = Project.objects.create(name="새 프로젝트")
        data = {
            "project": new_project.id,
            "sales_type": "DESIGN_CHANGE",
            "sales_received_date": "2024-02-01",
            "estimate_request_date": "2024-02-05",
            "estimate_expected_date": "2024-02-10",
            "estimate_submit_date": "2024-02-15",
            "estimate_amount": "2000000.00",
            "design_amount": "1000000.00",
        }
        response = self.client.post('/api/project-sales/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['sales_type'], data['sales_type'])

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(ProjectSales.objects.filter(sales_type=data['sales_type']).exists())

    def test_create_project_sales_with_invalid_type(self):
        """영업 생성 API 테스트 - 잘못된 sales_type 값"""
        new_project = Project.objects.create(name="잘못된 타입 프로젝트")
        data = {
            "project": new_project.id,
            "sales_type": "INVALID_TYPE",
        }
        response = self.client.post('/api/project-sales/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = self._get_response_data(response)
        self.assertFalse(response_data['success'])


    # ========== UPDATE ==========
    def test_update_project_sales(self):
        """영업 전체 수정 API 테스트 (Update - PUT)"""
        data = {
            "project": self.project.id,
            "sales_type": "TECHNICAL_PROPOSAL",
            "sales_received_date": "2024-03-01",
            "estimate_amount": "3000000.00",
        }
        response = self.client.put(
            f'/api/project-sales/{self.sales.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.sales.refresh_from_db()
        self.assertEqual(self.sales.sales_type, "TECHNICAL_PROPOSAL")

    def test_partial_update_project_sales(self):
        """영업 부분 수정 API 테스트 (Update - PATCH)"""
        data = {
            "sales_type": "PRIVATE_INVESTMENT",
        }
        response = self.client.patch(
            f'/api/project-sales/{self.sales.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.sales.refresh_from_db()
        self.assertEqual(self.sales.sales_type, "PRIVATE_INVESTMENT")

    # ========== DELETE ==========
    def test_delete_project_sales(self):
        """영업 삭제 API 테스트 (Delete - 204 No Content)"""
        sales_id = self.sales.id
        response = self.client.delete(f'/api/project-sales/{sales_id}/')

        # 204 No Content 응답 확인
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')

        # 소프트 삭제 확인
        self.sales.refresh_from_db()
        self.assertIsNotNone(self.sales.deleted_at)
        self.assertTrue(self.sales.is_deleted)

    # ========== 커스텀 액션 ==========
    def test_by_project_action(self):
        """프로젝트별 영업 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/project-sales/by-project/{self.project.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_by_type_action(self):
        """영업 유형별 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get('/api/project-sales/by-type/METHOD_REVIEW/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])


class SalesAssigneeAPITest(APITestCase):
    """SalesAssignee API 통합 테스트 - CRUD 모두 포함"""

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
        cls.sales = ProjectSales.objects.create(
            project=cls.project,
            sales_type="METHOD_REVIEW",
        )
        cls.assignee = SalesAssignee.objects.create(
            sales=cls.sales,
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
    def test_list_sales_assignees(self):
        """영업 담당자 목록 조회 API 테스트 (Read)"""
        response = self.client.get('/api/sales-assignees/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_retrieve_sales_assignee(self):
        """영업 담당자 상세 조회 API 테스트 (Read)"""
        response = self.client.get(f'/api/sales-assignees/{self.assignee.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.assignee.id)
        self.assertEqual(response_data['data']['is_primary'], True)

    # ========== CREATE ==========
    def test_create_sales_assignee(self):
        """영업 담당자 생성 API 테스트 (Create)"""
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
            "sales": self.sales.id,
            "user": new_user.id,
            "is_primary": False,
        }
        response = self.client.post('/api/sales-assignees/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(
            SalesAssignee.objects.filter(
                sales=self.sales,
                user=new_user
            ).exists()
        )

    def test_create_sales_assignee_duplicate(self):
        """영업 담당자 중복 생성 시도 테스트"""
        data = {
            "sales": self.sales.id,
            "user": self.user.id,  # 이미 존재하는 사용자
            "is_primary": False,
        }
        response = self.client.post('/api/sales-assignees/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = self._get_response_data(response)
        self.assertFalse(response_data['success'])

    def test_create_sales_assignee_multiple_primary(self):
        """영업 담당자 여러 명을 주요 담당자로 지정 시도 테스트"""
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
            "sales": self.sales.id,
            "user": new_user.id,
            "is_primary": True,  # 이미 주요 담당자가 있음
        }
        response = self.client.post('/api/sales-assignees/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = self._get_response_data(response)
        self.assertFalse(response_data['success'])

    # ========== DELETE ==========
    def test_delete_sales_assignee(self):
        """영업 담당자 삭제 API 테스트 (Delete - 204 No Content)"""
        assignee_id = self.assignee.id
        response = self.client.delete(f'/api/sales-assignees/{assignee_id}/')

        # 204 No Content 응답 확인
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 소프트 삭제 확인
        self.assignee.refresh_from_db()
        self.assertIsNotNone(self.assignee.deleted_at)
        self.assertTrue(self.assignee.is_deleted)

    # ========== 커스텀 액션 ==========
    def test_by_sales_action(self):
        """영업별 담당자 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/sales-assignees/by-sales/{self.sales.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_primary_action(self):
        """영업의 주요 담당자 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/sales-assignees/primary/{self.sales.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['is_primary'], True)

    def test_by_user_action(self):
        """사용자별 영업 할당 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/sales-assignees/by-user/{self.user.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])


class SalesHistoryAPITest(APITestCase):
    """SalesHistory API 통합 테스트 - CRUD 모두 포함"""

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
        cls.sales = ProjectSales.objects.create(
            project=cls.project,
            sales_type="METHOD_REVIEW",
        )
        cls.history = SalesHistory.objects.create(
            sales=cls.sales,
            user=cls.user,
            content="테스트 이력 내용",
            is_public=True,
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
    def test_list_sales_histories(self):
        """영업 이력 목록 조회 API 테스트 (Read)"""
        response = self.client.get('/api/sales-histories/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_retrieve_sales_history(self):
        """영업 이력 상세 조회 API 테스트 (Read)"""
        response = self.client.get(f'/api/sales-histories/{self.history.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.history.id)
        self.assertEqual(response_data['data']['content'], self.history.content)
        self.assertEqual(response_data['data']['is_public'], True)

    # ========== CREATE ==========
    def test_create_sales_history(self):
        """영업 이력 생성 API 테스트 (Create)"""
        data = {
            "sales": self.sales.id,
            "user": self.user.id,
            "content": "새 이력 내용",
            "is_public": False,
        }
        response = self.client.post('/api/sales-histories/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(
            SalesHistory.objects.filter(
                sales=self.sales,
                content=data['content']
            ).exists()
        )

    # ========== UPDATE ==========
    def test_partial_update_sales_history(self):
        """영업 이력 부분 수정 API 테스트 (Update - PATCH)"""
        data = {
            "is_public": False,
        }
        response = self.client.patch(
            f'/api/sales-histories/{self.history.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.history.refresh_from_db()
        self.assertEqual(self.history.is_public, False)

    # ========== DELETE ==========
    def test_delete_sales_history(self):
        """영업 이력 삭제 API 테스트 (Delete - 204 No Content)"""
        history_id = self.history.id
        response = self.client.delete(f'/api/sales-histories/{history_id}/')

        # 204 No Content 응답 확인
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 소프트 삭제 확인
        self.history.refresh_from_db()
        self.assertIsNotNone(self.history.deleted_at)
        self.assertTrue(self.history.is_deleted)

    # ========== 커스텀 액션 ==========
    def test_by_sales_action(self):
        """영업별 이력 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/sales-histories/by-sales/{self.sales.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_public_action(self):
        """영업의 공개 이력 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/sales-histories/public/{self.sales.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_by_user_action(self):
        """사용자별 영업 이력 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/sales-histories/by-user/{self.user.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])