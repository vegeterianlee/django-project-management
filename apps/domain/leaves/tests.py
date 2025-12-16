"""
Leaves Domain Tests

- 모델 테스트: TestCase 사용
- API 테스트: APITestCase 사용
- CRUD: Create, Read(List/Retrieve), Update(전체/부분), Delete 모두 포함
"""
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
import json

from apps.domain.leaves.models import LeaveGrant, LeaveRequest, LeaveUsage
from apps.domain.users.models import User, Department, Position
from apps.domain.company.models import Company
from apps.domain.approvals.models import ApprovalRequest

# ============================================
# 모델 단위 테스트 - TestCase 사용
# ============================================
class LeaveGrantModelTest(TestCase):
    """LeaveGrant 모델 단위 테스트"""

    @classmethod
    def setUpTestData(cls):
        cls.company = Company.objects.create(
            name='회사명',
            type="client"
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
        cls.leave_grant = LeaveGrant.objects.create(
            user=cls.user,
            grant_type='ANNUAL',
            total_days=Decimal('15.00'),
            remaining_days=Decimal('15.00'),
            granted_at=timezone.now(),  # ✅ DateTimeField이므로 timezone.now() 사용
            expires_at=date.today() + timedelta(days=365)
        )

    def test_leave_grant_creation(self):
        self.assertIsNotNone(self.leave_grant.id)
        self.assertEqual(self.leave_grant.grant_type, 'ANNUAL')
        self.assertEqual(self.leave_grant.total_days, Decimal('15.00'))
        self.assertEqual(self.leave_grant.remaining_days, Decimal('15.00'))

    def test_leave_grant_soft_delete(self):
        self.leave_grant.delete()
        self.leave_grant.refresh_from_db()
        self.assertEqual(self.leave_grant.is_deleted, True)
        self.assertTrue(self.leave_grant.deleted_at)


class LeaveRequestModelTest(TestCase):
    """LeaveRequest 모델 단위 테스트"""

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
        cls.delegate_user = User.objects.create(
            user_uid="test_user_002",
            name="위임 사용자",
            email="delegate@example.com",
            position_id=cls.position.id,
            department_id=cls.department.id,
            company=cls.company,
            password="hashed_password",
        )

        # ApprovalRequest를 먼저 생성 (임시 request_type_id 사용)
        cls.approval_request = ApprovalRequest.objects.create(
            requester=cls.user,
            request_type='LEAVE',
            request_type_id=999,  # 임시 값
            status='PENDING'
        )

        cls.leave_request = LeaveRequest.objects.create(
            user=cls.user,
            approval_request=cls.approval_request,  # ✅ 필수 필드
            leave_type='ANNUAL',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            total_days=Decimal('3.00'),
            reason="개인 사정",
            delegate_user=cls.delegate_user,  # ✅ delegate_user 객체 사용
            status='PENDING'
        )

        # request_type_id를 실제 leave_request.id로 업데이트
        cls.approval_request.request_type_id = cls.leave_request.id
        cls.approval_request.save()

    def test_leave_request_creation(self):
        """LeaveRequest 생성 테스트"""
        self.assertIsNotNone(self.leave_request.id)
        self.assertEqual(self.leave_request.leave_type, 'ANNUAL')
        self.assertEqual(self.leave_request.status, 'PENDING')
        self.assertEqual(self.leave_request.delegate_user, self.delegate_user)
        self.assertEqual(self.leave_request.approval_request, self.approval_request)

    def test_leave_request_half_day_validation(self):
        """반차 검증 테스트"""
        # ApprovalRequest 먼저 생성
        approval_request = ApprovalRequest.objects.create(
            requester=self.user,
            request_type='LEAVE',
            request_type_id=999,  # 임시 값
            status='PENDING'
        )

        # 반차는 하루만 가능 (잘못된 경우: 다음날)
        half_day_request = LeaveRequest(
            user=self.user,
            approval_request=approval_request,  # ✅ 필수 필드
            leave_type='HALF_MORNING',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1),  # 다음날 (잘못됨)
            total_days=Decimal('0.5'),
            reason="개인 사정",
            delegate_user=self.delegate_user,  # ✅ delegate_user 객체 사용
            status='PENDING'
        )
        with self.assertRaises(Exception):
            half_day_request.full_clean()
            half_day_request.save()

class LeaveUsageModelTest(TestCase):
    """LeaveUsage 모델 단위 테스트"""

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
        cls.delegate_user = User.objects.create(
            user_uid="test_user_002",
            name="위임 사용자",
            email="delegate@example.com",
            position_id=cls.position.id,
            department_id=cls.department.id,
            company=cls.company,
            password="hashed_password",
        )

        # ApprovalRequest 생성
        cls.approval_request = ApprovalRequest.objects.create(
            requester=cls.user,
            request_type='LEAVE',
            request_type_id=999,  # 임시 값
            status='APPROVED',
            approved_at=timezone.now()
        )

        cls.leave_grant = LeaveGrant.objects.create(
            user=cls.user,
            grant_type='ANNUAL',
            total_days=Decimal('15.00'),
            remaining_days=Decimal('15.00'),
            granted_at=timezone.now(),  # ✅ DateTimeField
            expires_at=date.today() + timedelta(days=365)
        )

        cls.leave_request = LeaveRequest.objects.create(
            user=cls.user,
            approval_request=cls.approval_request,  # ✅ 필수 필드
            leave_type='ANNUAL',
            start_date=date.today(),
            end_date=date.today(),
            total_days=Decimal('1.00'),
            reason="개인 사정",
            delegate_user=cls.delegate_user,  # ✅ delegate_user 객체 사용
            status='APPROVED'
        )

        # request_type_id 업데이트
        cls.approval_request.request_type_id = cls.leave_request.id
        cls.approval_request.save()

        cls.leave_usage = LeaveUsage.objects.create(
            user=cls.user,
            leave_grant=cls.leave_grant,
            leave_request=cls.leave_request,
            used_days=Decimal('1.00'),
            used_date=date.today()
        )

    def test_leave_usage_creation(self):
        """LeaveUsage 생성 테스트"""
        self.assertIsNotNone(self.leave_usage.id)
        self.assertEqual(self.leave_usage.used_days, Decimal('1.00'))
        self.assertEqual(self.leave_usage.leave_grant, self.leave_grant)
        self.assertEqual(self.leave_usage.leave_request, self.leave_request)


# ============================================
# API 통합 테스트 - APITestCase 사용
# ============================================
class LeaveRequestAPITest(APITestCase):
    """LeaveRequest API 통합 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.company = Company.objects.create(
            name="테스트 회사",
            type="CLIENT",
        )
        cls.department = Department.objects.create(
            name="개발팀",
            organization_type='TECH'
        )
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
        cls.delegate_user = User.objects.create(
            user_uid="test_user_002",
            name="위임 사용자",
            email="delegate@example.com",
            position_id=cls.position.id,
            department_id=cls.department.id,
            company=cls.company,
            password="hashed_password",
        )
        # 휴가 지급 (잔액 확보)
        cls.leave_grant = LeaveGrant.objects.create(
            user=cls.user,
            grant_type='ANNUAL',
            total_days=Decimal('15.00'),
            remaining_days=Decimal('15.00'),
            granted_at=timezone.now(),  # ✅ DateTimeField
            expires_at=date.today() + timedelta(days=365)
        )

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def _get_response_data(self, response):
        """BaseJsonResponse에서 데이터를 추출하는 헬퍼 메서드"""
        if response.status_code == status.HTTP_204_NO_CONTENT:
            return None

        print("response", response)
        if hasattr(response, 'content') and response.content:
            try:
                print("response_content", response.content.decode('utf-8'))
                return json.loads(response.content.decode('utf-8'))
            except json.JSONDecodeError:
                return {}

        print("response_data", response.data)
        return response.data

    def test_list_leave_requests(self):
        """휴가 신청 목록 조회 API 테스트"""
        response = self.client.get('/api/leave-requests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_retrieve_leave_request(self):
        """휴가 신청 상세 조회 API 테스트"""
        # ApprovalRequest 생성
        approval_request = ApprovalRequest.objects.create(
            requester=self.user,
            request_type='LEAVE',
            request_type_id=999,
            status='PENDING'
        )

        leave_request = LeaveRequest.objects.create(
            user=self.user,
            approval_request=approval_request,  # ✅ 필수 필드
            leave_type='ANNUAL',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            total_days=Decimal('3.00'),
            reason="개인 사정",
            delegate_user=self.delegate_user,
            status='PENDING'
        )

        # request_type_id 업데이트
        approval_request.request_type_id = leave_request.id
        approval_request.save()

        response = self.client.get(f'/api/leave-requests/{leave_request.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], leave_request.id)

    # ========== CREATE ==========
    def test_create_leave_request(self):
        """휴가 신청 생성 API 테스트 (결재 요청 포함)"""
        data = {
            "leave_type": "ANNUAL",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=2)).isoformat(),
            "total_days": "3.00",
            "reason": "개인 사정",
            "delegate_user": self.delegate_user.id,
        }
        response = self.client.post('/api/leave-requests/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        # DB에 실제로 생성되었는지 확인
        self.assertTrue(LeaveRequest.objects.filter(user=self.user).exists())
        # ApprovalRequest도 생성되었는지 확인
        leave_request = LeaveRequest.objects.get(user=self.user)
        self.assertIsNotNone(leave_request.approval_request)

    def test_create_half_day_leave_request(self):
        """반차 신청 생성 API 테스트"""
        data = {
            "leave_type": "HALF_MORNING",
            "start_date": date.today().isoformat(),
            "end_date": date.today().isoformat(),  # 같은 날
            "total_days": "0.5",
            "reason": "오전 반차",
            "delegate_user": self.delegate_user.id,
        }
        response = self.client.post('/api/leave-requests/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    # ========== UPDATE ==========
    def test_partial_update_leave_request(self):
        """휴가 신청 부분 수정 API 테스트 (승인 전)"""
        # ApprovalRequest 생성
        approval_request = ApprovalRequest.objects.create(
            requester=self.user,
            request_type='LEAVE',
            request_type_id=999,
            status='PENDING'
        )

        leave_request = LeaveRequest.objects.create(
            user=self.user,
            approval_request=approval_request,  # ✅ 필수 필드
            leave_type='ANNUAL',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            total_days=Decimal('3.00'),
            reason="개인 사정",
            delegate_user=self.delegate_user,
            status='PENDING'
        )

        # request_type_id 업데이트
        approval_request.request_type_id = leave_request.id
        approval_request.save()

        data = {"reason": "수정된 사유"}
        response = self.client.patch(
            f'/api/leave-requests/{leave_request.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        leave_request.refresh_from_db()
        self.assertEqual(leave_request.reason, "수정된 사유")

    def test_partial_update_approved_leave_request_fails(self):
        """승인된 휴가 신청 수정 불가 테스트"""
        # ApprovalRequest 생성
        approval_request = ApprovalRequest.objects.create(
            requester=self.user,
            request_type='LEAVE',
            request_type_id=999,
            status='APPROVED'
        )

        leave_request = LeaveRequest.objects.create(
            user=self.user,
            approval_request=approval_request,  # ✅ 필수 필드
            leave_type='ANNUAL',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            total_days=Decimal('3.00'),
            reason="개인 사정",
            delegate_user=self.delegate_user,
            status='APPROVED',
            approved_at=timezone.now()
        )

        # request_type_id 업데이트
        approval_request.request_type_id = leave_request.id
        approval_request.save()

        data = {"reason": "수정 시도"}
        response = self.client.patch(
            f'/api/leave-requests/{leave_request.id}/',
            data,
            format='json'
        )

        # 승인된 경우 수정 불가
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ========== DELETE ==========
    def test_delete_leave_request(self):
        """휴가 신청 삭제 API 테스트"""
        # ApprovalRequest 생성
        approval_request = ApprovalRequest.objects.create(
            requester=self.user,
            request_type='LEAVE',
            request_type_id=999,
            status='PENDING'
        )

        leave_request = LeaveRequest.objects.create(
            user=self.user,
            approval_request=approval_request,  # ✅ 필수 필드
            leave_type='ANNUAL',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            total_days=Decimal('3.00'),
            reason="개인 사정",
            delegate_user=self.delegate_user,
            status='PENDING'
        )

        # request_type_id 업데이트
        approval_request.request_type_id = leave_request.id
        approval_request.save()

        response = self.client.delete(f'/api/leave-requests/{leave_request.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        leave_request.refresh_from_db()
        self.assertIsNotNone(leave_request.deleted_at)

    # ========== CUSTOM ACTIONS ==========
    def test_cancel_leave_request(self):
        """휴가 신청 취소 API 테스트"""
        # ApprovalRequest 생성
        approval_request = ApprovalRequest.objects.create(
            requester=self.user,
            request_type='LEAVE',
            request_type_id=999,
            status='PENDING'
        )

        leave_request = LeaveRequest.objects.create(
            user=self.user,
            approval_request=approval_request,  # ✅ 필수 필드
            leave_type='ANNUAL',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            total_days=Decimal('3.00'),
            reason="개인 사정",
            delegate_user=self.delegate_user,
            status='PENDING'
        )

        # request_type_id 업데이트
        approval_request.request_type_id = leave_request.id
        approval_request.save()

        data = {"cancel_reason": "취소 사유"}
        response = self.client.post(
            f'/api/leave-requests/{leave_request.id}/cancel/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        leave_request.refresh_from_db()
        self.assertEqual(leave_request.status, 'CANCELLED')


class LeaveGrantAPITest(APITestCase):
    """LeaveGrant API 통합 테스트"""

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
        cls.leave_grant = LeaveGrant.objects.create(
            user=cls.user,
            grant_type='ANNUAL',
            total_days=Decimal('15.00'),
            remaining_days=Decimal('15.00'),
            granted_at=timezone.now(),  # ✅ DateTimeField
            expires_at=date.today() + timedelta(days=365)
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

    def test_list_leave_grants(self):
        """휴가 지급 목록 조회 API 테스트"""
        response = self.client.get('/api/leave-grants/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_retrieve_leave_grant(self):
        """휴가 지급 상세 조회 API 테스트"""
        response = self.client.get(f'/api/leave-grants/{self.leave_grant.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.leave_grant.id)


class LeaveUsageAPITest(APITestCase):
    """LeaveUsage API 통합 테스트"""

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
        cls.delegate_user = User.objects.create(
            user_uid="test_user_002",
            name="위임 사용자",
            email="delegate@example.com",
            position_id=cls.position.id,
            department_id=cls.department.id,
            company=cls.company,
            password="hashed_password",
        )

        # ApprovalRequest 생성
        cls.approval_request = ApprovalRequest.objects.create(
            requester=cls.user,
            request_type='LEAVE',
            request_type_id=999,
            status='APPROVED',
            approved_at=timezone.now()
        )

        cls.leave_grant = LeaveGrant.objects.create(
            user=cls.user,
            grant_type='ANNUAL',
            total_days=Decimal('15.00'),
            remaining_days=Decimal('15.00'),
            granted_at=timezone.now(),  # ✅ DateTimeField
            expires_at=date.today() + timedelta(days=365)
        )

        cls.leave_request = LeaveRequest.objects.create(
            user=cls.user,
            approval_request=cls.approval_request,  # ✅ 필수 필드
            leave_type='ANNUAL',
            start_date=date.today(),
            end_date=date.today(),
            total_days=Decimal('1.00'),
            reason="개인 사정",
            delegate_user=cls.delegate_user,  # ✅ delegate_user 객체 사용
            status='APPROVED'
        )

        # request_type_id 업데이트
        cls.approval_request.request_type_id = cls.leave_request.id
        cls.approval_request.save()

        cls.leave_usage = LeaveUsage.objects.create(
            user=cls.user,
            leave_grant=cls.leave_grant,
            leave_request=cls.leave_request,
            used_days=Decimal('1.00'),
            used_date=date.today()
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

    def test_list_leave_usages(self):
        """휴가 사용 목록 조회 API 테스트"""
        response = self.client.get('/api/leave-usages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_retrieve_leave_usage(self):
        """휴가 사용 상세 조회 API 테스트"""
        response = self.client.get(f'/api/leave-usages/{self.leave_usage.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.leave_usage.id)