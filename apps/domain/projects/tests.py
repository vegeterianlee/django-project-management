"""
Projects Domain Tests

- 모델 테스트: TestCase 사용
- API 테스트: APITestCase 사용
- CRUD: Create, Read(List/Retrieve), Update(전체/부분), Delete 모두 포함
"""
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
import json
from datetime import date

from apps.domain.projects.models import Project, ProjectCompanyLink, ProjectAssignee, ProjectMethod
from apps.domain.company.models import Company
from apps.domain.users.models import User, Department, Position


# ============================================
# 모델 단위 테스트 - TestCase 사용
# ============================================
class ProjectModelTest(TestCase):
    """Project 모델 단위 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.project = Project.objects.create(
            project_code="PRJ001",
            name="테스트 프로젝트",
            description="테스트 프로젝트 설명",
            status="PLANNING",  # ✅ Enum 값으로 변경
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

    def test_project_creation(self):
        """Project 생성 테스트"""
        self.assertIsNotNone(self.project.id)
        self.assertEqual(self.project.project_code, "PRJ001")
        self.assertEqual(self.project.name, "테스트 프로젝트")
        self.assertEqual(self.project.status, "PLANNING")

    def test_project_soft_delete(self):
        """Project 소프트 삭제 테스트"""
        project_id = self.project.id
        self.project.delete()

        self.project.refresh_from_db()
        self.assertIsNotNone(self.project.deleted_at)
        self.assertTrue(self.project.is_deleted)

    def test_project_str(self):
        """Project __str__ 메서드 테스트"""
        self.assertEqual(str(self.project), "테스트 프로젝트")


class ProjectMethodModelTest(TestCase):
    """ProjectMethod 모델 단위 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.project = Project.objects.create(
            name="테스트 프로젝트",
        )
        cls.method = ProjectMethod.objects.create(
            project=cls.project,
            method="GRB",
        )

    def test_project_method_creation(self):
        """ProjectMethod 생성 테스트"""
        self.assertIsNotNone(self.method.id)
        self.assertEqual(self.method.project, self.project)
        self.assertEqual(self.method.method, "GRB")

    def test_project_method_unique_constraint(self):
        """ProjectMethod 고유 제약 조건 테스트"""
        # 같은 프로젝트에 같은 공법으로 중복 생성 시도
        with self.assertRaises(Exception):  # IntegrityError
            ProjectMethod.objects.create(
                project=self.project,
                method="GRB",
            )

    def test_project_method_soft_delete(self):
        """ProjectMethod 소프트 삭제 테스트"""
        self.method.delete()
        self.method.refresh_from_db()
        self.assertIsNotNone(self.method.deleted_at)
        self.assertTrue(self.method.is_deleted)


class ProjectCompanyLinkModelTest(TestCase):
    """ProjectCompanyLink 모델 단위 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.company = Company.objects.create(
            name="테스트 회사",
            type="CLIENT",
        )
        cls.project = Project.objects.create(
            name="테스트 프로젝트",
        )
        cls.link = ProjectCompanyLink.objects.create(
            project=cls.project,
            company=cls.company,
            role="CLIENT",
        )

    def test_project_company_link_creation(self):
        """ProjectCompanyLink 생성 테스트"""
        self.assertIsNotNone(self.link.id)
        self.assertEqual(self.link.project, self.project)
        self.assertEqual(self.link.company, self.company)
        self.assertEqual(self.link.role, "CLIENT")

    def test_project_company_link_unique_constraint(self):
        """ProjectCompanyLink 고유 제약 조건 테스트"""
        # 같은 프로젝트에 같은 역할로 중복 생성 시도
        with self.assertRaises(Exception):  # IntegrityError
            ProjectCompanyLink.objects.create(
                project=self.project,
                company=self.company,
                role="CLIENT",
            )


class ProjectAssigneeModelTest(TestCase):
    """ProjectAssignee 모델 단위 테스트"""

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
        cls.project = Project.objects.create(
            name="테스트 프로젝트",
        )
        cls.assignee = ProjectAssignee.objects.create(
            project=cls.project,
            user=cls.user,
            is_primary=True,
        )

    def test_project_assignee_creation(self):
        """ProjectAssignee 생성 테스트"""
        self.assertIsNotNone(self.assignee.id)
        self.assertEqual(self.assignee.project, self.project)
        self.assertEqual(self.assignee.user, self.user)
        self.assertTrue(self.assignee.is_primary)

    def test_project_assignee_unique_constraint(self):
        """ProjectAssignee 고유 제약 조건 테스트"""
        # 같은 프로젝트에 같은 사용자로 중복 생성 시도
        with self.assertRaises(Exception):  # IntegrityError
            ProjectAssignee.objects.create(
                project=self.project,
                user=self.user,
                is_primary=False,
            )


# ============================================
# API 통합 테스트 - APITestCase 사용
# ============================================
class ProjectAPITest(APITestCase):
    """Project API 통합 테스트 - CRUD 모두 포함"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.project = Project.objects.create(
            project_code="PRJ001",
            name="테스트 프로젝트",
            description="테스트 프로젝트 설명",
            status="PLANNING",  # ✅ Enum 값으로 변경
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
        # ProjectMethod 추가
        cls.method1 = ProjectMethod.objects.create(
            project=cls.project,
            method="GRB",
        )
        cls.method2 = ProjectMethod.objects.create(
            project=cls.project,
            method="GTCIP",
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
    def test_list_projects(self):
        """프로젝트 목록 조회 API 테스트 (Read)"""
        response = self.client.get('/api/projects/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)

    def test_list_projects_pagination(self):
        """프로젝트 목록 페이지네이션 테스트 (Read)"""
        # 여러 프로젝트 생성
        for i in range(15):
            Project.objects.create(
                name=f"프로젝트 {i + 1}",
                status="PLANNING",
            )

        response = self.client.get('/api/projects/', {'page': 1, 'page_size': 10})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_retrieve_project(self):
        """프로젝트 상세 조회 API 테스트 (Read)"""
        response = self.client.get(f'/api/projects/{self.project.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.project.id)
        self.assertEqual(response_data['data']['name'], self.project.name)
        # methods 필드 확인
        self.assertIn('methods', response_data['data'])
        self.assertIn('methods_list', response_data['data'])
        self.assertEqual(len(response_data['data']['methods']), 2)
        self.assertEqual(len(response_data['data']['methods_list']), 2)

    # ========== CREATE ==========
    def test_create_project(self):
        """프로젝트 생성 API 테스트 (Create) - methods 없이"""
        data = {
            "project_code": "PRJ002",
            "name": "새 프로젝트",
            "description": "새 프로젝트 설명",
            "status": "PLANNING",
            "start_date": "2024-06-01",
            "end_date": "2024-12-31",
        }
        response = self.client.post('/api/projects/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['name'], data['name'])

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(Project.objects.filter(project_code=data['project_code']).exists())

    def test_create_project_with_methods(self):
        """프로젝트 생성 API 테스트 (Create) - methods와 함께"""
        data = {
            "project_code": "PRJ003",
            "name": "공법 포함 프로젝트",
            "description": "공법 포함 프로젝트 설명",
            "status": "PLANNING",
            "start_date": "2024-06-01",
            "end_date": "2024-12-31",
            "methods_input": ["GRB", "GTCIP", "PSF"],  # ✅ methods_input 추가
        }
        response = self.client.post('/api/projects/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['name'], data['name'])

        # DB에 실제로 생성되었는지 확인
        project = Project.objects.get(project_code=data['project_code'])
        self.assertIsNotNone(project)

        # ProjectMethod가 실제로 생성되었는지 확인
        methods = ProjectMethod.objects.filter(project=project, deleted_at__isnull=True)
        self.assertEqual(methods.count(), 3)
        method_values = list(methods.values_list('method', flat=True))
        self.assertIn("GRB", method_values)
        self.assertIn("GTCIP", method_values)
        self.assertIn("PSF", method_values)

        # 응답에 methods가 포함되어 있는지 확인
        self.assertIn('methods', response_data['data'])
        self.assertEqual(len(response_data['data']['methods']), 3)
        self.assertEqual(len(response_data['data']['methods_list']), 3)

    def test_create_project_with_invalid_methods(self):
        """프로젝트 생성 API 테스트 - 잘못된 methods 값"""
        data = {
            "project_code": "PRJ004",
            "name": "잘못된 공법 프로젝트",
            "status": "PLANNING",
            "methods_input": ["INVALID_METHOD"],  # ✅ 잘못된 공법 값
        }
        response = self.client.post('/api/projects/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = self._get_response_data(response)
        self.assertFalse(response_data['success'])
        self.assertIn('methods_input', response_data.get('data', {}))

    def test_create_project_with_duplicate_methods(self):
        """프로젝트 생성 API 테스트 - 중복된 methods"""
        data = {
            "project_code": "PRJ005",
            "name": "중복 공법 프로젝트",
            "status": "PLANNING",
            "methods_input": ["GRB", "GRB"],  # ✅ 중복된 공법
        }
        response = self.client.post('/api/projects/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = self._get_response_data(response)
        self.assertFalse(response_data['success'])

    # ========== UPDATE ==========
    def test_update_project(self):
        """프로젝트 전체 수정 API 테스트 (Update - PUT)"""
        data = {
            "project_code": "PRJ001",
            "name": "수정된 프로젝트",
            "description": "수정된 프로젝트 설명",
            "status": "IN_PROGRESS",  # ✅ Enum 값으로 변경
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        }
        response = self.client.put(
            f'/api/projects/{self.project.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "수정된 프로젝트")
        self.assertEqual(self.project.status, "IN_PROGRESS")

    def test_update_project_with_methods(self):
        """프로젝트 전체 수정 API 테스트 - methods 업데이트 포함"""
        data = {
            "project_code": "PRJ001",
            "name": "수정된 프로젝트",
            "description": "수정된 프로젝트 설명",
            "status": "IN_PROGRESS",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "methods_input": ["PSF", "UNIONBRIDGE"],  # ✅ methods 업데이트
        }
        response = self.client.put(
            f'/api/projects/{self.project.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "수정된 프로젝트")

        # methods가 업데이트되었는지 확인
        methods = ProjectMethod.objects.filter(project=self.project, deleted_at__isnull=True)
        method_values = list(methods.values_list('method', flat=True))
        self.assertIn("PSF", method_values)
        self.assertIn("UNIONBRIDGE", method_values)
        # 기존 methods는 삭제되었는지 확인
        self.assertNotIn("GRB", method_values)
        self.assertNotIn("GTCIP", method_values)

    def test_partial_update_project(self):
        """프로젝트 부분 수정 API 테스트 (Update - PATCH)"""
        data = {"status": "ON_HOLD"}  # ✅ Enum 값으로 변경
        response = self.client.patch(
            f'/api/projects/{self.project.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, "ON_HOLD")
        # 다른 필드는 변경되지 않았는지 확인
        self.assertEqual(self.project.name, "테스트 프로젝트")

    def test_partial_update_project_with_methods(self):
        """프로젝트 부분 수정 API 테스트 - methods만 업데이트"""
        data = {"methods_input": ["GROSSBLOCK"]}
        response = self.client.patch(
            f'/api/projects/{self.project.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # methods가 업데이트되었는지 확인
        methods = ProjectMethod.objects.filter(project=self.project, deleted_at__isnull=True)
        method_values = list(methods.values_list('method', flat=True))
        self.assertEqual(len(method_values), 1)
        self.assertIn("GROSSBLOCK", method_values)

    # ========== DELETE ==========
    def test_delete_project(self):
        """프로젝트 삭제 API 테스트 (Delete - 204 No Content)"""
        project_id = self.project.id
        response = self.client.delete(f'/api/projects/{project_id}/')

        # 204 No Content 응답 확인 (본문 없음)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # 204 응답은 본문이 없으므로 JSON 파싱 시도하지 않음
        self.assertEqual(response.content, b'')  # 빈 본문 확인

        # 소프트 삭제 확인
        self.project.refresh_from_db()
        self.assertIsNotNone(self.project.deleted_at)
        self.assertTrue(self.project.is_deleted)


# ============================================
# ProjectMethod API 테스트
# ============================================
class ProjectMethodAPITest(APITestCase):
    """ProjectMethod API 통합 테스트 - CRUD 모두 포함"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.project = Project.objects.create(
            name="테스트 프로젝트",
        )
        cls.method = ProjectMethod.objects.create(
            project=cls.project,
            method="GRB",
        )

    def _get_response_data(self, response):
        """
        BaseJsonResponse에서 데이터를 추출하는 헬퍼 메서드

        204 No Content 응답은 본문이 없으므로 처리하지 않음
        """
        if response.status_code == status.HTTP_204_NO_CONTENT:
            return None

        if hasattr(response, 'content') and response.content:
            try:
                return json.loads(response.content.decode('utf-8'))
            except json.JSONDecodeError:
                return {}
        return response.data

    # ========== READ ==========
    def test_list_project_methods(self):
        """프로젝트-공법 연결 목록 조회 API 테스트 (Read)"""
        response = self.client.get('/api/project-methods/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)

    def test_retrieve_project_method(self):
        """프로젝트-공법 연결 상세 조회 API 테스트 (Read)"""
        response = self.client.get(f'/api/project-methods/{self.method.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.method.id)
        self.assertEqual(response_data['data']['method'], self.method.method)

    # ========== CREATE ==========
    def test_create_project_method(self):
        """프로젝트-공법 연결 생성 API 테스트 (Create)"""
        # 새로운 프로젝트 생성
        new_project = Project.objects.create(name="새 프로젝트")

        data = {
            "project": new_project.id,
            "method": "GTCIP",
        }
        response = self.client.post('/api/project-methods/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['method'], data['method'])

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(
            ProjectMethod.objects.filter(
                project=new_project,
                method="GTCIP"
            ).exists()
        )

    def test_create_project_method_duplicate(self):
        """프로젝트-공법 연결 중복 생성 시도 테스트"""
        data = {
            "project": self.project.id,
            "method": "GRB",  # 이미 존재하는 공법
        }
        response = self.client.post('/api/project-methods/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = self._get_response_data(response)
        self.assertFalse(response_data['success'])

    # ========== UPDATE ==========
    def test_update_project_method(self):
        """프로젝트-공법 연결 전체 수정 API 테스트 (Update - PUT)"""
        data = {
            "project": self.project.id,
            "method": "PSF",
        }
        response = self.client.put(
            f'/api/project-methods/{self.method.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.method.refresh_from_db()
        self.assertEqual(self.method.method, "PSF")

    def test_partial_update_project_method(self):
        """프로젝트-공법 연결 부분 수정 API 테스트 (Update - PATCH)"""
        data = {"method": "UNIONPC"}
        response = self.client.patch(
            f'/api/project-methods/{self.method.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.method.refresh_from_db()
        self.assertEqual(self.method.method, "UNIONPC")

    # ========== DELETE ==========
    def test_delete_project_method(self):
        """프로젝트-공법 연결 삭제 API 테스트 (Delete - 204 No Content)"""
        method_id = self.method.id
        response = self.client.delete(f'/api/project-methods/{method_id}/')

        # 204 No Content 응답 확인 (본문 없음)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')  # 빈 본문 확인

        # 소프트 삭제 확인
        self.method.refresh_from_db()
        self.assertIsNotNone(self.method.deleted_at)
        self.assertTrue(self.method.is_deleted)

    # ========== 커스텀 액션 ==========
    def test_by_project_action(self):
        """프로젝트별 공법 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/project-methods/by-project/{self.project.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)

    def test_by_method_action(self):
        """공법별 프로젝트 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get('/api/project-methods/by-method/GRB/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])


# ============================================
# ProjectCompanyLink API 테스트
# ============================================
class ProjectCompanyLinkAPITest(APITestCase):
    """ProjectCompanyLink API 통합 테스트 - CRUD 모두 포함"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.company = Company.objects.create(
            name="테스트 회사",
            type="CLIENT",
        )
        cls.project = Project.objects.create(
            name="테스트 프로젝트",
        )
        cls.link = ProjectCompanyLink.objects.create(
            project=cls.project,
            company=cls.company,
            role="CLIENT",
        )

    def _get_response_data(self, response):
        """
        BaseJsonResponse에서 데이터를 추출하는 헬퍼 메서드

        204 No Content 응답은 본문이 없으므로 처리하지 않음
        """
        if response.status_code == status.HTTP_204_NO_CONTENT:
            return None

        if hasattr(response, 'content') and response.content:
            try:
                return json.loads(response.content.decode('utf-8'))
            except json.JSONDecodeError:
                return {}
        return response.data

    # ========== READ ==========
    def test_list_project_company_links(self):
        """프로젝트-회사 연결 목록 조회 API 테스트 (Read)"""
        response = self.client.get('/api/project-company-links/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)

    def test_retrieve_project_company_link(self):
        """프로젝트-회사 연결 상세 조회 API 테스트 (Read)"""
        response = self.client.get(f'/api/project-company-links/{self.link.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.link.id)
        self.assertEqual(response_data['data']['role'], self.link.role)

    # ========== CREATE ==========
    def test_create_project_company_link(self):
        """프로젝트-회사 연결 생성 API 테스트 (Create)"""
        # 새로운 프로젝트와 회사 생성
        new_project = Project.objects.create(name="새 프로젝트")
        new_company = Company.objects.create(name="새 회사", type="DESIGN")

        data = {
            "project": new_project.id,
            "company": new_company.id,
            "role": "DESIGN",
        }
        response = self.client.post('/api/project-company-links/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['role'], data['role'])

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(
            ProjectCompanyLink.objects.filter(
                project=new_project,
                company=new_company,
                role="DESIGN"
            ).exists()
        )

    # ========== UPDATE ==========
    def test_update_project_company_link(self):
        """프로젝트-회사 연결 전체 수정 API 테스트 (Update - PUT)"""
        # 새로운 회사 생성
        new_company = Company.objects.create(name="수정된 회사", type="CONSTRUCTION")

        data = {
            "project": self.project.id,
            "company": new_company.id,
            "role": "CONSTRUCTION",
        }
        response = self.client.put(
            f'/api/project-company-links/{self.link.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.link.refresh_from_db()
        self.assertEqual(self.link.company.id, new_company.id)
        self.assertEqual(self.link.role, "CONSTRUCTION")

    def test_partial_update_project_company_link(self):
        """프로젝트-회사 연결 부분 수정 API 테스트 (Update - PATCH)"""
        data = {"role": "DESIGN"}
        response = self.client.patch(
            f'/api/project-company-links/{self.link.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.link.refresh_from_db()
        self.assertEqual(self.link.role, "DESIGN")
        # 다른 필드는 변경되지 않았는지 확인
        self.assertEqual(self.link.company.id, self.company.id)

    # ========== DELETE ==========
    def test_delete_project_company_link(self):
        """프로젝트-회사 연결 삭제 API 테스트 (Delete - 204 No Content)"""
        link_id = self.link.id
        response = self.client.delete(f'/api/project-company-links/{link_id}/')

        # 204 No Content 응답 확인 (본문 없음)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')  # 빈 본문 확인

        # 소프트 삭제 확인
        self.link.refresh_from_db()
        self.assertIsNotNone(self.link.deleted_at)
        self.assertTrue(self.link.is_deleted)

    # ========== 커스텀 액션 ==========
    def test_by_project_action(self):
        """프로젝트별 회사 연결 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/project-company-links/by-project/{self.project.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)

    def test_by_role_action(self):
        """역할별 프로젝트-회사 연결 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get('/api/project-company-links/by-role/CLIENT/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_by_company_action(self):
        """회사별 프로젝트 연결 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/project-company-links/by-company/{self.company.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])


# ============================================
# ProjectAssignee API 테스트
# ============================================
class ProjectAssigneeAPITest(APITestCase):
    """ProjectAssignee API 통합 테스트 - CRUD 모두 포함"""

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
        cls.project = Project.objects.create(
            name="테스트 프로젝트",
        )
        cls.assignee = ProjectAssignee.objects.create(
            project=cls.project,
            user=cls.user,
            is_primary=True,
        )

    def _get_response_data(self, response):
        """
        BaseJsonResponse에서 데이터를 추출하는 헬퍼 메서드

        204 No Content 응답은 본문이 없으므로 처리하지 않음
        """
        if response.status_code == status.HTTP_204_NO_CONTENT:
            return None

        if hasattr(response, 'content') and response.content:
            try:
                return json.loads(response.content.decode('utf-8'))
            except json.JSONDecodeError:
                return {}
        return response.data

    # ========== READ ==========
    def test_list_project_assignees(self):
        """프로젝트 담당자 목록 조회 API 테스트 (Read)"""
        response = self.client.get('/api/project-assignees/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)

    def test_retrieve_project_assignee(self):
        """프로젝트 담당자 상세 조회 API 테스트 (Read)"""
        response = self.client.get(f'/api/project-assignees/{self.assignee.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.assignee.id)
        self.assertEqual(response_data['data']['is_primary'], self.assignee.is_primary)

    # ========== CREATE ==========
    def test_create_project_assignee(self):
        """프로젝트 담당자 생성 API 테스트 (Create)"""
        # 새로운 프로젝트와 사용자 생성
        new_project = Project.objects.create(name="새 프로젝트")
        new_user = User.objects.create(
            user_uid="test_user_002",
            name="새 사용자",
            email="new@example.com",
            position_id=self.position.id,
            department_id=self.department.id,
            company=self.company,
            password="hashed_password",
        )

        data = {
            "project": new_project.id,
            "user": new_user.id,
            "is_primary": False,
        }
        response = self.client.post('/api/project-assignees/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['is_primary'], data['is_primary'])

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(
            ProjectAssignee.objects.filter(
                project=new_project,
                user=new_user
            ).exists()
        )

    # ========== UPDATE ==========
    def test_update_project_assignee(self):
        """프로젝트 담당자 전체 수정 API 테스트 (Update - PUT)"""
        # 새로운 사용자 생성
        new_user = User.objects.create(
            user_uid="test_user_003",
            name="수정된 사용자",
            email="updated@example.com",
            position_id=self.position.id,
            department_id=self.department.id,
            company=self.company,
            password="hashed_password",
        )

        data = {
            "project": self.project.id,
            "user": new_user.id,
            "is_primary": False,
        }
        response = self.client.put(
            f'/api/project-assignees/{self.assignee.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.assignee.refresh_from_db()
        self.assertEqual(self.assignee.user.id, new_user.id)
        self.assertEqual(self.assignee.is_primary, False)

    def test_partial_update_project_assignee(self):
        """프로젝트 담당자 부분 수정 API 테스트 (Update - PATCH)"""
        data = {"is_primary": False}
        response = self.client.patch(
            f'/api/project-assignees/{self.assignee.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.assignee.refresh_from_db()
        self.assertEqual(self.assignee.is_primary, False)
        # 다른 필드는 변경되지 않았는지 확인
        self.assertEqual(self.assignee.user.id, self.user.id)

    # ========== DELETE ==========
    def test_delete_project_assignee(self):
        """프로젝트 담당자 삭제 API 테스트 (Delete - 204 No Content)"""
        assignee_id = self.assignee.id
        response = self.client.delete(f'/api/project-assignees/{assignee_id}/')

        # 204 No Content 응답 확인 (본문 없음)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')  # 빈 본문 확인

        # 소프트 삭제 확인
        self.assignee.refresh_from_db()
        self.assertIsNotNone(self.assignee.deleted_at)
        self.assertTrue(self.assignee.is_deleted)

    # ========== 커스텀 액션 ==========
    def test_by_project_action(self):
        """프로젝트별 담당자 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/project-assignees/by-project/{self.project.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)

    def test_primary_action(self):
        """프로젝트의 주요 담당자 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/project-assignees/primary/{self.project.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['is_primary'], True)

    def test_by_user_action(self):
        """사용자별 프로젝트 할당 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(f'/api/project-assignees/by-user/{self.user.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])