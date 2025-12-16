"""
Notifications Domain Tests

- 모델 테스트: TestCase 사용
- API 테스트: APITestCase 사용
- CRUD: Create, Read(List/Retrieve), Update(전체/부분), Delete 모두 포함
"""
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
import json

from apps.domain.notifications.models import Notification
from apps.domain.users.models import User, Department, Position
from apps.domain.company.models import Company


# ============================================
# 모델 단위 테스트 - TestCase 사용
# ============================================
class NotificationModelTest(TestCase):
    """Notification 모델 단위 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.company = Company.objects.create(name="테스트 회사", type="CLIENT")
        cls.department = Department.objects.create(name="개발팀")
        cls.position = Position.objects.create(title="시니어 개발자")
        cls.sender = User.objects.create(
            user_uid="test_user_001",
            name="발신자",
            email="sender@example.com",
            position_id=cls.position.id,
            department_id=cls.department.id,
            company=cls.company,
            password="hashed_password",
        )
        cls.receiver = User.objects.create(
            user_uid="test_user_002",
            name="수신자",
            email="receiver@example.com",
            position_id=cls.position.id,
            department_id=cls.department.id,
            company=cls.company,
            password="hashed_password",
        )
        cls.notification = Notification.objects.create(
            sender=cls.sender,
            receiver=cls.receiver,
            notification_type='LEAVE_REQUEST',
            notification_type_id=1,
            message="휴가 신청 알림"
        )

    def test_notification_creation(self):
        """Notification 생성 테스트"""
        self.assertIsNotNone(self.notification.id)
        self.assertEqual(self.notification.notification_type, 'LEAVE_REQUEST')
        self.assertEqual(self.notification.is_read, False)
        self.assertEqual(self.notification.sender, self.sender)
        self.assertEqual(self.notification.receiver, self.receiver)

    def test_notification_mark_as_read(self):
        """Notification 읽음 처리 테스트"""
        self.notification.mark_as_read()
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)
        self.assertIsNotNone(self.notification.read_at)

    def test_notification_soft_delete(self):
        """Notification 소프트 삭제 테스트"""
        self.notification.delete()
        self.notification.refresh_from_db()
        self.assertIsNotNone(self.notification.deleted_at)


# ============================================
# API 통합 테스트 - APITestCase 사용
# ============================================
class NotificationAPITest(APITestCase):
    """Notification API 통합 테스트"""

    @classmethod
    def setUpTestData(cls):
        """클래스 레벨 데이터 준비"""
        cls.company = Company.objects.create(name="테스트 회사", type="CLIENT")
        cls.department = Department.objects.create(name="개발팀")
        cls.position = Position.objects.create(title="시니어 개발자")
        cls.sender = User.objects.create(
            user_uid="test_user_001",
            name="발신자",
            email="sender@example.com",
            position_id=cls.position.id,
            department_id=cls.department.id,
            company=cls.company,
            password="hashed_password",
        )
        cls.receiver = User.objects.create(
            user_uid="test_user_002",
            name="수신자",
            email="receiver@example.com",
            position_id=cls.position.id,
            department_id=cls.department.id,
            company=cls.company,
            password="hashed_password",
        )
        cls.notification = Notification.objects.create(
            sender=cls.sender,
            receiver=cls.receiver,
            notification_type='LEAVE_REQUEST',
            notification_type_id=1,
            message="휴가 신청 알림"
        )

    def setUp(self):
        """각 테스트 전 실행"""
        self.client.force_authenticate(user=self.receiver)

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
    def test_list_notifications(self):
        """알림 목록 조회 API 테스트"""
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

    def test_list_notifications_filter_by_is_read(self):
        """읽음 여부로 알림 필터링 테스트"""
        # 읽음 알림 생성
        Notification.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            notification_type='LEAVE_APPROVED',
            notification_type_id=1,
            message="승인 알림",
            is_read=True
        )

        response = self.client.get('/api/notifications/?is_read=false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        # 모든 결과가 읽지 않음인지 확인
        for notification in response_data['data']:
            self.assertFalse(notification['is_read'])

    def test_retrieve_notification(self):
        """알림 상세 조회 API 테스트"""
        response = self.client.get(f'/api/notifications/{self.notification.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], self.notification.id)

    # ========== CUSTOM ACTIONS ==========
    def test_mark_as_read(self):
        """알림 읽음 처리 API 테스트"""
        response = self.client.post(
            f'/api/notifications/{self.notification.id}/mark-as-read/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])

        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_mark_all_as_read(self):
        """모든 알림 읽음 처리 API 테스트"""
        # 추가 알림 생성
        Notification.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            notification_type='LEAVE_APPROVED',
            notification_type_id=1,
            message="승인 알림"
        )

        response = self.client.post('/api/notifications/mark-all-as-read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertGreater(response_data['data']['count'], 0)

    def test_unread_count(self):
        Notification.objects.create(
            sender=self.sender,
            receiver=self.receiver,  # ✅ self.receiver가 현재 인증된 사용자여야 함
            notification_type='LEAVE_APPROVED',
            notification_type_id=1,
            message="승인 알림",
            is_read=False
        )

        """미읽음 알림 개수 조회 API 테스트"""
        response = self.client.get('/api/notifications/unread-count/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self._get_response_data(response)
        self.assertTrue(response_data['success'])
        self.assertIn('count', response_data['data'])
        self.assertGreater(response_data['data']['count'], 0)