"""
Users Domain Tests

- 모델 테스트: TestCase 사용
- API 테스트: APITestCase 사용
- CRUD: Create, Read(List/Retrieve), Update(전체/부분), Delete 모두 포함
"""
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
import json
from urllib.parse import quote

from apps.domain.users.models import User, Department, Position, UserPermission
from apps.domain.company.models import Company


# ============================================
# 모델 단위 테스트 - TestCase 사용
# ============================================
class UserModelTest(TestCase):
    """User 모델 단위 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.company = Company.objects.create(
            name="테스트 회사",
            type="CLIENT",
        )
        cls.department = Department.objects.create(name="개발팀")
        cls.position = Position.objects.create(
            title="시니어 개발자",
            hierarchy_level=5,
        )
        cls.user = User.objects.create(
            user_uid="test_user_001",
            name="테스트 사용자",
            email="test@example.com",
            position_id=cls.position.id,
            department_id=cls.department.id,
            company=cls.company,
            password="hashed_password",
        )

    def test_user_creation(self):
        """User 생성 테스트"""
        self.assertIsNotNone(self.user.id)
        self.assertEqual(self.user.user_uid, "test_user_001")
        self.assertEqual(self.user.email, "test@example.com")

    def test_user_soft_delete(self):
        """User 소프트 삭제 테스트"""
        self.user.delete()

        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.deleted_at)
        self.assertTrue(self.user.is_deleted)


class DepartmentModelTest(TestCase):
    """Department 모델 단위 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.department = Department.objects.create(
            name="개발팀",
            description="소프트웨어 개발 부서",
        )

    def test_department_creation(self):
        """Department 생성 테스트"""
        self.assertIsNotNone(self.department.id)
        self.assertEqual(self.department.name, "개발팀")

    def test_department_unique_name(self):
        """Department 이름 고유성 테스트"""
        with self.assertRaises(Exception):  # IntegrityError
            Department.objects.create(name="개발팀")


class PositionModelTest(TestCase):
    """Position 모델 단위 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.position = Position.objects.create(
            title="시니어 개발자",
            hierarchy_level=5,
            is_executive=False,
        )

    def test_position_creation(self):
        """Position 생성 테스트"""
        self.assertIsNotNone(self.position.id)
        self.assertEqual(self.position.title, "시니어 개발자")
        self.assertEqual(self.position.hierarchy_level, 5)


# ============================================
# API 통합 테스트 - APITestCase 사용
# ============================================
class UserAPITest(APITestCase):
    """User API 통합 테스트 - CRUD 모두 포함"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.company = Company.objects.create(
            name="테스트 회사",
            type="CLIENT",
        )
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

    def _get_response_data(self, response):
        """
        BaseJsonResponse에서 데이터를 추출하는 헬퍼 메서드

        204 No Content 응답은 본문이 없으므로 처리하지 않음
        """
        # 204 No Content는 본문이 없음
        if response.status_code == status.HTTP_204_NO_CONTENT:
            return None

        if hasattr(response, 'content') and response.content:
            try:
                return json.loads(response.content.decode('utf-8'))
            except json.JSONDecodeError:
                return {}
        return response.data

    # ========== READ ==========
    def test_list_users(self):
        """사용자 목록 조회 API 테스트 (Read)"""
        response = self.client.get('/api/users/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_list_users_pagination(self):
        """사용자 목록 페이지네이션 테스트 (Read)"""
        # 테스트별 추가 데이터 생성
        for i in range(15):
            User.objects.create(
                user_uid=f"user_{i + 1}",
                name=f"사용자 {i + 1}",
                email=f"user{i + 1}@example.com",
                position_id=self.position.id,
                department_id=self.department.id,
                password="hashed_password",
            )

        response = self.client.get('/api/users/', {'page': 1, 'page_size': 10})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_retrieve_user(self):
        """사용자 상세 조회 API 테스트 (Read)"""
        response = self.client.get(f'/api/users/{self.user.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.user.id)

    # ========== CREATE ==========
    def test_create_user(self):
        """사용자 생성 API 테스트 (Create)"""
        data = {
            "user_uid": "new_user_001",
            "name": "새 사용자",
            "email": "new@example.com",
            "position_id": self.position.id,
            "department_id": self.department.id,
            "company": self.company.id,
            "password": "hashed_password",
        }
        response = self.client.post('/api/users/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(User.objects.filter(user_uid=data['user_uid']).exists())

    # ========== UPDATE ==========
    def test_update_user(self):
        """사용자 전체 수정 API 테스트 (Update - PUT)"""
        data = {
            "user_uid": "test_user_001",
            "name": "수정된 사용자",
            "email": "updated@example.com",
            "position_id": self.position.id,
            "department_id": self.department.id,
            "company": self.company.id,
            "password": "new_hashed_password",
        }
        response = self.client.put(
            f'/api/users/{self.user.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "수정된 사용자")
        self.assertEqual(self.user.email, "updated@example.com")

    def test_partial_update_user(self):
        """사용자 부분 수정 API 테스트 (Update - PATCH)"""
        data = {"name": "부분 수정된 사용자"}
        response = self.client.patch(
            f'/api/users/{self.user.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "부분 수정된 사용자")
        # 다른 필드는 변경되지 않았는지 확인
        self.assertEqual(self.user.email, "test@example.com")

    # ========== DELETE ==========
    def test_delete_user(self):
        """사용자 삭제 API 테스트 (Delete - 204 No Content)"""
        user_id = self.user.id
        response = self.client.delete(f'/api/users/{user_id}/')

        # 204 No Content 응답 확인 (본문 없음)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # 204 응답은 본문이 없으므로 JSON 파싱 시도하지 않음
        self.assertEqual(response.content, b'')  # 빈 본문 확인

        # 소프트 삭제 확인
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.deleted_at)
        self.assertTrue(self.user.is_deleted)

    # ========== CUSTOM ACTIONS ==========
    def test_by_email_action(self):
        """이메일로 사용자 조회 API 테스트 (커스텀 액션)"""
        # 이메일을 URL 인코딩
        encoded_email = quote(self.user.email, safe='')
        response = self.client.get(f'/api/users/by-email/{encoded_email}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        # 응답이 단일 객체인지 리스트인지 확인
        if isinstance(response_data['data'], list):
            self.assertEqual(len(response_data['data']), 1)
            self.assertEqual(response_data['data'][0]['email'], self.user.email)
        else:
            self.assertEqual(response_data['data']['email'], self.user.email)

    def test_by_company_action(self):
        """회사별 사용자 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/users/by-company/{self.company.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIsInstance(response_data['data'], list)
        self.assertGreater(len(response_data['data']), 0)


class DepartmentAPITest(APITestCase):
    """Department API 통합 테스트 - CRUD 모두 포함"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.department = Department.objects.create(
            name="개발팀",
            description="소프트웨어 개발 부서",
        )

    def _get_response_data(self, response):
        """BaseJsonResponse에서 데이터를 추출하는 헬퍼 메서드"""
        # 204 No Content는 본문이 없음
        if response.status_code == status.HTTP_204_NO_CONTENT:
            return None

        if hasattr(response, 'content') and response.content:
            try:
                return json.loads(response.content.decode('utf-8'))
            except json.JSONDecodeError:
                return {}
        return response.data

    # ========== READ ==========
    def test_list_departments(self):
        """부서 목록 조회 API 테스트 (Read)"""
        response = self.client.get('/api/departments/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_retrieve_department(self):
        """부서 상세 조회 API 테스트 (Read)"""
        response = self.client.get(f'/api/departments/{self.department.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.department.id)
        self.assertEqual(response_data['data']['name'], self.department.name)

    # ========== CREATE ==========
    def test_create_department(self):
        """부서 생성 API 테스트 (Create)"""
        data = {
            "name": "디자인팀",
            "description": "디자인 부서",
        }
        response = self.client.post('/api/departments/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(Department.objects.filter(name=data['name']).exists())

    # ========== UPDATE ==========
    def test_update_department(self):
        """부서 전체 수정 API 테스트 (Update - PUT)"""
        data = {
            "name": "개발팀",
            "description": "수정된 개발 부서",
        }
        response = self.client.put(
            f'/api/departments/{self.department.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.department.refresh_from_db()
        self.assertEqual(self.department.description, "수정된 개발 부서")

    def test_partial_update_department(self):
        """부서 부분 수정 API 테스트 (Update - PATCH)"""
        data = {"description": "부분 수정된 부서 설명"}
        response = self.client.patch(
            f'/api/departments/{self.department.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.department.refresh_from_db()
        self.assertEqual(self.department.description, "부분 수정된 부서 설명")
        # 다른 필드는 변경되지 않았는지 확인
        self.assertEqual(self.department.name, "개발팀")

    # ========== DELETE ==========
    def test_delete_department(self):
        """부서 삭제 API 테스트 (Delete - 204 No Content)"""
        department_id = self.department.id
        response = self.client.delete(f'/api/departments/{department_id}/')

        # 204 No Content 응답 확인 (본문 없음)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # 204 응답은 본문이 없으므로 JSON 파싱 시도하지 않음
        self.assertEqual(response.content, b'')  # 빈 본문 확인

        # 실제로 삭제되었는지 확인 (하드 삭제)
        self.assertFalse(Department.objects.filter(id=department_id).exists())


class PositionAPITest(APITestCase):
    """Position API 통합 테스트 - CRUD 모두 포함"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.position = Position.objects.create(
            title="시니어 개발자",
            hierarchy_level=5,
            is_executive=False,
        )

    def _get_response_data(self, response):
        """BaseJsonResponse에서 데이터를 추출하는 헬퍼 메서드"""
        # 204 No Content는 본문이 없음
        if response.status_code == status.HTTP_204_NO_CONTENT:
            return None

        if hasattr(response, 'content') and response.content:
            try:
                return json.loads(response.content.decode('utf-8'))
            except json.JSONDecodeError:
                return {}
        return response.data

    # ========== READ ==========
    def test_list_positions(self):
        """직급 목록 조회 API 테스트 (Read)"""
        response = self.client.get('/api/positions/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_retrieve_position(self):
        """직급 상세 조회 API 테스트 (Read)"""
        response = self.client.get(f'/api/positions/{self.position.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.position.id)
        self.assertEqual(response_data['data']['title'], self.position.title)

    # ========== CREATE ==========
    def test_create_position(self):
        """직급 생성 API 테스트 (Create)"""
        data = {
            "title": "주니어 개발자",
            "hierarchy_level": 3,
            "is_executive": False,
            "description": "주니어 레벨 개발자",
        }
        response = self.client.post('/api/positions/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(Position.objects.filter(title=data['title']).exists())

    # ========== UPDATE ==========
    def test_update_position(self):
        """직급 전체 수정 API 테스트 (Update - PUT)"""
        data = {
            "title": "시니어 개발자",
            "hierarchy_level": 6,
            "is_executive": False,
            "description": "수정된 시니어 개발자",
        }
        response = self.client.put(
            f'/api/positions/{self.position.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.position.refresh_from_db()
        self.assertEqual(self.position.hierarchy_level, 6)

    def test_partial_update_position(self):
        """직급 부분 수정 API 테스트 (Update - PATCH)"""
        data = {"hierarchy_level": 7}
        response = self.client.patch(
            f'/api/positions/{self.position.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.position.refresh_from_db()
        self.assertEqual(self.position.hierarchy_level, 7)
        # 다른 필드는 변경되지 않았는지 확인
        self.assertEqual(self.position.title, "시니어 개발자")

    # ========== DELETE ==========
    def test_delete_position(self):
        """직급 삭제 API 테스트 (Delete - 204 No Content)"""
        position_id = self.position.id
        response = self.client.delete(f'/api/positions/{position_id}/')

        # 204 No Content 응답 확인 (본문 없음)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # 204 응답은 본문이 없으므로 JSON 파싱 시도하지 않음
        self.assertEqual(response.content, b'')  # 빈 본문 확인

        # 실제로 삭제되었는지 확인 (하드 삭제)
        self.assertFalse(Position.objects.filter(id=position_id).exists())

    # ========== CUSTOM ACTIONS ==========
    def test_executives_action(self):
        """임원 직급 조회 API 테스트 (커스텀 액션)"""
        # 임원 직급 생성
        Position.objects.create(
            title="임원",
            hierarchy_level=10,
            is_executive=True,
        )

        response = self.client.get('/api/positions/executives/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIsInstance(response_data['data'], list)

        # 모든 결과가 임원인지 확인
        for position in response_data['data']:
            self.assertTrue(position['is_executive'])