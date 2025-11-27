"""
Company Domain Tests

- 모델 테스트: TestCase 사용
- API 테스트: APITestCase 사용
- CRUD: Create, Read(List/Retrieve), Update(전체/부분), Delete 모두 포함
"""
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
import json

from apps.domain.company.models import Company, ContactPerson


# ============================================
# 모델 단위 테스트 - TestCase 사용
# ============================================
class CompanyModelTest(TestCase):
    """Company 모델 단위 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.company = Company.objects.create(
            name="테스트 회사",
            type="CLIENT",
            email="test@company.com",
            contact_number="02-1234-5678",
        )

    def test_company_creation(self):
        """Company 생성 테스트"""
        self.assertIsNotNone(self.company.id)
        self.assertEqual(self.company.name, "테스트 회사")
        self.assertEqual(self.company.type, "CLIENT")

    def test_company_soft_delete(self):
        """Company 소프트 삭제 테스트"""
        company_id = self.company.id
        self.company.delete()

        self.company.refresh_from_db()
        self.assertIsNotNone(self.company.deleted_at)
        self.assertTrue(self.company.is_deleted)

    def test_company_str(self):
        """Company __str__ 메서드 테스트"""
        self.assertEqual(str(self.company), "테스트 회사")


class ContactPersonModelTest(TestCase):
    """ContactPerson 모델 단위 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.company = Company.objects.create(
            name="테스트 회사",
            type="CLIENT",
        )
        cls.contact_person = ContactPerson.objects.create(
            name="담당자",
            email="contact@company.com",
            department_id=1,
            position_id=1,
            company=cls.company,
            is_primary=True,
        )

    def test_contact_person_creation(self):
        """ContactPerson 생성 테스트"""
        self.assertIsNotNone(self.contact_person.id)
        self.assertEqual(self.contact_person.company, self.company)


# ============================================
# API 통합 테스트 - APITestCase 사용
# ============================================
class CompanyAPITest(APITestCase):
    """Company API 통합 테스트 - CRUD 모두 포함"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.company = Company.objects.create(
            name="테스트 회사",
            type="CLIENT",
            email="test@company.com",
            contact_number="02-1234-5678",
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
    def test_list_companies(self):
        """회사 목록 조회 API 테스트 (Read)"""
        response = self.client.get('/api/companies/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)

    def test_list_companies_pagination(self):
        """회사 목록 페이지네이션 테스트 (Read)"""
        # 여러 회사 생성
        for i in range(15):
            Company.objects.create(
                name=f"회사 {i + 1}",
                type="CLIENT",
            )

        response = self.client.get('/api/companies/', {'page': 1, 'page_size': 10})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_retrieve_company(self):
        """회사 상세 조회 API 테스트 (Read)"""
        response = self.client.get(f'/api/companies/{self.company.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.company.id)
        self.assertEqual(response_data['data']['name'], self.company.name)

    # ========== CREATE ==========
    def test_create_company(self):
        """회사 생성 API 테스트 (Create)"""
        data = {
            "name": "새 회사",
            "type": "DESIGN",
            "email": "new@company.com",
            "contact_number": "02-9876-5432",
        }
        response = self.client.post('/api/companies/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['name'], data['name'])

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(Company.objects.filter(name=data['name']).exists())

    # ========== UPDATE ==========
    def test_update_company(self):
        """회사 전체 수정 API 테스트 (Update - PUT)"""
        data = {
            "name": "수정된 회사명",
            "type": "CLIENT",
            "email": "updated@company.com",
            "contact_number": "02-9999-8888",
        }
        response = self.client.put(
            f'/api/companies/{self.company.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.company.refresh_from_db()
        self.assertEqual(self.company.name, "수정된 회사명")
        self.assertEqual(self.company.email, "updated@company.com")

    def test_partial_update_company(self):
        """회사 부분 수정 API 테스트 (Update - PATCH)"""
        data = {"email": "patched@company.com"}
        response = self.client.patch(
            f'/api/companies/{self.company.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.company.refresh_from_db()
        self.assertEqual(self.company.email, "patched@company.com")
        # 다른 필드는 변경되지 않았는지 확인
        self.assertEqual(self.company.name, "테스트 회사")

    # ========== DELETE ==========
    def test_delete_company(self):
        """회사 삭제 API 테스트 (Delete - 204 No Content)"""
        company_id = self.company.id
        response = self.client.delete(f'/api/companies/{company_id}/')

        # 204 No Content 응답 확인 (본문 없음)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # 204 응답은 본문이 없으므로 JSON 파싱 시도하지 않음
        self.assertEqual(response.content, b'')  # 빈 본문 확인

        # 소프트 삭제 확인 (DB에서 실제로 deleted_at이 설정되었는지 확인)
        self.company.refresh_from_db()
        self.assertIsNotNone(self.company.deleted_at)
        self.assertTrue(self.company.is_deleted)

    # ========== CUSTOM ACTIONS ==========
    def test_by_type_action(self):
        """회사 타입별 조회 API 테스트 (커스텀 액션)"""
        # DESIGN 타입 회사 추가 생성
        Company.objects.create(
            name="디자인 회사",
            type="DESIGN",
        )

        response = self.client.get('/api/companies/by-type/CLIENT/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIsInstance(response_data['data'], list)
        self.assertGreater(len(response_data['data']), 0)

        # 모든 결과가 CLIENT 타입인지 확인
        for company in response_data['data']:
            self.assertEqual(company['type'], 'CLIENT')


class ContactPersonAPITest(APITestCase):
    """ContactPerson API 통합 테스트 - CRUD 모두 포함"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.company = Company.objects.create(
            name="테스트 회사",
            type="CLIENT",
        )
        cls.contact_person = ContactPerson.objects.create(
            name="담당자",
            email="contact@company.com",
            department_id=1,
            position_id=1,
            company=cls.company,
            is_primary=True,
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
    def test_list_contact_persons(self):
        """연락 담당자 목록 조회 API 테스트 (Read)"""
        response = self.client.get('/api/contact-persons/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_retrieve_contact_person(self):
        """연락 담당자 상세 조회 API 테스트 (Read)"""
        response = self.client.get(f'/api/contact-persons/{self.contact_person.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.contact_person.id)
        self.assertEqual(response_data['data']['name'], self.contact_person.name)

    # ========== CREATE ==========
    def test_create_contact_person(self):
        """연락 담당자 생성 API 테스트 (Create)"""
        data = {
            "name": "새 담당자",
            "email": "new@company.com",
            "department_id": 1,
            "position_id": 1,
            "company": self.company.id,
            "is_primary": False,
        }
        response = self.client.post('/api/contact-persons/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(ContactPerson.objects.filter(email=data['email']).exists())

    # ========== UPDATE ==========
    def test_update_contact_person(self):
        """연락 담당자 전체 수정 API 테스트 (Update - PUT)"""
        data = {
            "name": "수정된 담당자",
            "email": "updated@company.com",
            "department_id": 1,
            "position_id": 1,
            "company": self.company.id,
            "is_primary": False,
        }
        response = self.client.put(
            f'/api/contact-persons/{self.contact_person.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.contact_person.refresh_from_db()
        self.assertEqual(self.contact_person.name, "수정된 담당자")
        self.assertEqual(self.contact_person.email, "updated@company.com")

    def test_partial_update_contact_person(self):
        """연락 담당자 부분 수정 API 테스트 (Update - PATCH)"""
        data = {"is_primary": False}
        response = self.client.patch(
            f'/api/contact-persons/{self.contact_person.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에서 실제로 수정되었는지 확인
        self.contact_person.refresh_from_db()
        self.assertFalse(self.contact_person.is_primary)
        # 다른 필드는 변경되지 않았는지 확인
        self.assertEqual(self.contact_person.name, "담당자")

    # ========== DELETE ==========
    def test_delete_contact_person(self):
        """연락 담당자 삭제 API 테스트 (Delete - 204 No Content)"""
        contact_person_id = self.contact_person.id
        response = self.client.delete(f'/api/contact-persons/{contact_person_id}/')

        # 204 No Content 응답 확인 (본문 없음)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # 204 응답은 본문이 없으므로 JSON 파싱 시도하지 않음
        self.assertEqual(response.content, b'')  # 빈 본문 확인

        # 소프트 삭제 확인
        self.contact_person.refresh_from_db()
        self.assertIsNotNone(self.contact_person.deleted_at)
        self.assertTrue(self.contact_person.is_deleted)

    # ========== CUSTOM ACTIONS ==========
    def test_by_company_action(self):
        """회사별 연락 담당자 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(
            f'/api/contact-persons/by-company/{self.company.id}/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIsInstance(response_data['data'], list)
        self.assertGreater(len(response_data['data']), 0)

    def test_primary_contact_action(self):
        """주요 연락 담당자 조회 API 테스트 (커스텀 액션)"""
        response = self.client.get(
            f'/api/contact-persons/primary/{self.company.id}/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertTrue(response_data['data']['is_primary'])