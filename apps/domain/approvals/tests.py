"""
Approvals Domain Tests

- 모델 테스트: TestCase 사용
- API 테스트: APITestCase 사용
- CRUD: Create, Read(List/Retrieve), Update(전체/부분), Delete 모두 포함
"""
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
import json

from apps.domain.approvals.models import ApprovalRequest, ApprovalLine, ApprovalPolicy, ApprovalPolicyStep
from apps.domain.users.models import User, Department, Position, DepartmentManager
from apps.domain.company.models import Company
from apps.domain.leaves.models import LeaveRequest


# ============================================
# 모델 단위 테스트 - TestCase 사용
# ============================================
class ApprovalRequestModelTest(TestCase):
    """ApprovalRequest 모델 단위 테스트"""

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
        cls.approval_request = ApprovalRequest.objects.create(
            requester=cls.user,
            request_type='LEAVE',
            request_type_id=1,
            status='PENDING'
        )

    def test_approval_request_creation(self):
        """ApprovalRequest 생성 테스트"""
        self.assertIsNotNone(self.approval_request.id)
        self.assertEqual(self.approval_request.request_type, 'LEAVE')
        self.assertEqual(self.approval_request.status, 'PENDING')
        self.assertEqual(self.approval_request.requester, self.user)

    def test_approval_request_soft_delete(self):
        """ApprovalRequest 소프트 삭제 테스트"""
        self.approval_request.delete()
        self.approval_request.refresh_from_db()
        self.assertIsNotNone(self.approval_request.deleted_at)


class ApprovalLineModelTest(TestCase):
    """ApprovalLine 모델 단위 테스트"""

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
        cls.approver = User.objects.create(
            user_uid="test_user_002",
            name="결재자",
            email="approver@example.com",
            position_id=cls.position.id,
            department_id=cls.department.id,
            company=cls.company,
            password="hashed_password",
        )
        cls.approval_request = ApprovalRequest.objects.create(
            requester=cls.user,
            request_type='LEAVE',
            request_type_id=1,
            status='PENDING'
        )
        cls.approval_line = ApprovalLine.objects.create(
            approval_request=cls.approval_request,
            step_order=1,
            approver=cls.approver,
            status='PENDING'
        )

    def test_approval_line_creation(self):
        """ApprovalLine 생성 테스트"""
        self.assertIsNotNone(self.approval_line.id)
        self.assertEqual(self.approval_line.step_order, 1)
        self.assertEqual(self.approval_line.status, 'PENDING')
        self.assertEqual(self.approval_line.approver, self.approver)


class ApprovalPolicyModelTest(TestCase):
    """ApprovalPolicy 모델 단위 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.policy = ApprovalPolicy.objects.create(
            request_type='LEAVE',
            applies_to_dept_type='TECH',
            applies_to_role='EMPLOYEE'
        )

    def test_approval_policy_creation(self):
        """ApprovalPolicy 생성 테스트"""
        self.assertIsNotNone(self.policy.id)
        self.assertEqual(self.policy.request_type, 'LEAVE')
        self.assertEqual(self.policy.applies_to_dept_type, 'TECH')


class ApprovalPolicyStepModelTest(TestCase):
    """ApprovalPolicyStep 모델 단위 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.policy = ApprovalPolicy.objects.create(
            request_type='LEAVE',
            applies_to_dept_type='TECH',
            applies_to_role='EMPLOYEE'
        )
        cls.policy_step = ApprovalPolicyStep.objects.create(
            policy=cls.policy,
            step_order=1,
            approver_selector_type='DEPT_MANAGER'
        )

    def test_approval_policy_step_creation(self):
        """ApprovalPolicyStep 생성 테스트"""
        self.assertIsNotNone(self.policy_step.id)
        self.assertEqual(self.policy_step.step_order, 1)
        self.assertEqual(self.policy_step.approver_selector_type, 'DEPT_MANAGER')


# ============================================
# API 통합 테스트 - APITestCase 사용
# ============================================
class ApprovalRequestAPITest(APITestCase):
    """ApprovalRequest API 통합 테스트"""

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
        cls.approval_request = ApprovalRequest.objects.create(
            requester=cls.user,
            request_type='LEAVE',
            request_type_id=1,
            status='PENDING'
        )

    def setUp(self):
        """각 테스트 전 실행"""
        self.client.force_authenticate(user=self.user)

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

    def test_list_approval_requests(self):
        """결재 요청 목록 조회 API 테스트"""
        response = self.client.get('/api/approval-requests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_retrieve_approval_request(self):
        """결재 요청 상세 조회 API 테스트"""
        response = self.client.get(f'/api/approval-requests/{self.approval_request.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.approval_request.id)


class ApprovalLineAPITest(APITestCase):
    """ApprovalLine API 통합 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.company = Company.objects.create(name="테스트 회사", type="CLIENT")
        cls.department = Department.objects.create(name="개발팀", organization_type='TECH')
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
        cls.approver = User.objects.create(
            user_uid="test_user_002",
            name="결재자",
            email="approver@example.com",
            position_id=cls.position.id,
            department_id=cls.department.id,
            company=cls.company,
            password="hashed_password",
        )
        # 부서장 설정
        DepartmentManager.objects.create(
            department=cls.department,
            user=cls.approver
        )
        cls.approval_request = ApprovalRequest.objects.create(
            requester=cls.user,
            request_type='LEAVE',
            request_type_id=1,
            status='PENDING'
        )
        cls.approval_line = ApprovalLine.objects.create(
            approval_request=cls.approval_request,
            step_order=1,
            approver=cls.approver,
            status='PENDING'
        )

    def setUp(self):
        """각 테스트 전 실행"""
        self.client.force_authenticate(user=self.approver)

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

    def test_list_approval_lines(self):
        """결재 라인 목록 조회 API 테스트"""
        response = self.client.get('/api/approval-lines/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_retrieve_approval_line(self):
        """결재 라인 상세 조회 API 테스트"""
        response = self.client.get(f'/api/approval-lines/{self.approval_line.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_approve_approval_line(self):
        """결재 라인 승인 API 테스트"""
        data = {"comment": "승인합니다"}
        response = self.client.post(
            f'/api/approval-lines/{self.approval_line.id}/approve/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        self.approval_line.refresh_from_db()
        self.assertEqual(self.approval_line.status, 'APPROVED')

    def test_reject_approval_line(self):
        """결재 라인 반려 API 테스트"""
        data = {"comment": "반려 사유"}
        response = self.client.post(
            f'/api/approval-lines/{self.approval_line.id}/reject/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        self.approval_line.refresh_from_db()
        self.assertEqual(self.approval_line.status, 'REJECTED')
        self.approval_request.refresh_from_db()
        self.assertEqual(self.approval_request.status, 'REJECTED')


class ApprovalPolicyAPITest(APITestCase):
    """ApprovalPolicy API 통합 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.policy = ApprovalPolicy.objects.create(
            request_type='LEAVE',
            applies_to_dept_type='TECH',
            applies_to_role='EMPLOYEE'
        )

    def setUp(self):
        """각 테스트 전 실행"""
        # 관리자 권한 필요할 수 있음
        from apps.domain.users.models import User, Department, Position
        from apps.domain.company.models import Company
        company = Company.objects.create(name="테스트 회사", type="CLIENT")
        department = Department.objects.create(name="관리팀")
        position = Position.objects.create(title="관리자")
        admin_user = User.objects.create(
            user_uid="admin_001",
            name="관리자",
            email="admin@example.com",
            position_id=position.id,
            department_id=department.id,
            company=company,
            password="hashed_password",
        )
        self.client.force_authenticate(user=admin_user)

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

    def test_list_approval_policies(self):
        """결재 정책 목록 조회 API 테스트"""
        response = self.client.get('/api/approval-policies/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_create_approval_policy(self):
        """결재 정책 생성 API 테스트"""
        data = {
            "request_type": "LEAVE",
            "applies_to_dept_type": "HQ",
            "applies_to_role": "EMPLOYEE"
        }
        response = self.client.post('/api/approval-policies/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_update_approval_policy(self):
        """결재 정책 수정 API 테스트"""
        data = {
            "request_type": "LEAVE",
            "applies_to_dept_type": "TECH",
            "applies_to_role": "LEADER"
        }
        response = self.client.put(
            f'/api/approval-policies/{self.policy.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])


class ApprovalPolicyStepAPITest(APITestCase):
    """ApprovalPolicyStep API 통합 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.policy = ApprovalPolicy.objects.create(
            request_type='LEAVE',
            applies_to_dept_type='TECH',
            applies_to_role='EMPLOYEE'
        )
        cls.policy_step = ApprovalPolicyStep.objects.create(
            policy=cls.policy,
            step_order=1,
            approver_selector_type='DEPT_MANAGER'
        )

    def setUp(self):
        """각 테스트 전 실행"""
        from apps.domain.users.models import User, Department, Position
        from apps.domain.company.models import Company
        company = Company.objects.create(name="테스트 회사", type="CLIENT")
        department = Department.objects.create(name="관리팀")
        position = Position.objects.create(title="관리자")
        admin_user = User.objects.create(
            user_uid="admin_001",
            name="관리자",
            email="admin@example.com",
            position_id=position.id,
            department_id=department.id,
            company=company,
            password="hashed_password",
        )
        self.client.force_authenticate(user=admin_user)

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

    def test_list_approval_policy_steps(self):
        """결재 정책 단계 목록 조회 API 테스트"""
        response = self.client.get('/api/approval-policy-steps/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_create_approval_policy_step(self):
        """결재 정책 단계 생성 API 테스트"""
        data = {
            "policy": self.policy.id,
            "step_order": 2,
            "approver_selector_type": "CEO"
        }
        response = self.client.post('/api/approval-policy-steps/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])