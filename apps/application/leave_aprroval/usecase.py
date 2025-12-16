"""
Leave Approval UseCase

휴가 결재 관련 유즈케이스를 처리합니다.
"""
from typing import Optional
from django.db import transaction
from apps.domain.leaves.service import LeaveService
from apps.domain.approvals.service import ApprovalService
from apps.domain.notifications.service import NotificationService
from apps.domain.leaves.models import LeaveRequest
from apps.domain.approvals.models import ApprovalRequest, ApprovalLine
from datetime import date
from decimal import Decimal
from apps.domain.users.models import User


class LeaveApprovalUseCase:
    """
    휴가 결재 관련 유즈케이스입니다.

    책임:
    - 휴가 신청 및 결재 라인 생성
    - 결재 승인/반려 처리
    - 결재 취소 처리 (승인 완료 후 취소 포함)
    """

    @staticmethod
    @transaction.atomic
    def create_leave_request_with_approval(
        user_id: int,
        leave_type: str,
        start_date: str,
        end_date: str,
        total_days: float,
        reason: str,
        delegate_user_id: int
    ) -> tuple[LeaveRequest, ApprovalRequest]:
        """
        휴가 신청과 결재 요청을 함께 생성
        """

        user = User.objects.get(id=user_id)

        # 1. LeaveRequest 생성
        leave_request = LeaveService.create_leave_request(
            user=user,
            leave_type=leave_type,
            start_date=date.fromisoformat(start_date),
            end_date=date.fromisoformat(end_date),
            total_days=Decimal(str(total_days)),
            reason=reason,
            delegate_user_id=delegate_user_id
        )

        # 2. ApprovalRequest 생성
        approval_request = ApprovalRequest.objects.create(
            requester=user,
            request_type='LEAVE',
            request_type_id=leave_request.id,
            status='PENDING'
        )

        # 3. LeaveRequest와 ApprovalRequest 연결
        leave_request.approval_request = approval_request
        leave_request.save(update_fields=['approval_request'])

        # 4. 결재 라인 생성
        approval_lines = ApprovalService.create_approval_lines(
            approval_request_id=approval_request.id,
        )

        # 5. 첫번째 결재자에게 알림 발송
        if approval_lines:
            first_approver = approval_lines[0].approver
            NotificationService.create_notification(
                sender_id=user_id,
                receiver_id=first_approver.id,
                notification_type="LEAVE_REQUEST",
                message=f"{user.name}님의 휴가 신청 결재 건입니다.",
                notification_type_id=approval_request.id
            )

        return leave_request, approval_request

    @staticmethod
    @transaction.atomic
    def approve_leave_request(
        approver_line_id: int,
        approver_user_id: int,
        comment: Optional[str] = None
    ) -> tuple[ApprovalLine, Optional[LeaveRequest]]:
        """
        결재 라인을 승인합니다.
        승인된 결재라인과 승인 완료된 경우 LeaveRequest를 반환합니다.

        :param approver_id:
        :param approver_user_id:
        :param comment:
        :return: tuple[ApprovalLine, Optional[LeaveRequest]]
        """

        # 결재 라인 숭인
        approval_line = ApprovalService.approve_approval_line(
            approval_line_id=approver_line_id,
            approver_user_id=approver_user_id,
            comment=comment
        )

        approval_request = approval_line.approval_request

        # 모든 결재 완료 시 LeaveUsage 생성
        leave_request = None
        if approval_request.status == 'APPROVED':
            try:
                # LeaveRequest 조회
                leave_request = approval_request.leave_request

                # 승인되도록 변경
                leave_request.status = 'APPROVED'
                leave_request.save(update_fields=['status'])

                # LeaveUsage 생성
                LeaveService.create_leave_usage(
                    leave_request_id=leave_request.id
                )

                # 신청자에게 승인 알림
                NotificationService.create_notification(
                    sender_id=approver_user_id,
                    receiver_id=approval_request.requester.id,
                    notification_type="LEAVE_APPROVED",
                    message=f"휴가 신청이 승인되었습니다.",
                    notification_type_id=leave_request.id
                )
            except LeaveRequest.DoesNotExist:
                pass

        # 3. 다음 결재자에게 알림 발송
        next_approver_line = ApprovalLine.objects.filter(
            approval_request=approval_request,
            step_order__gt=approval_line.step_order,
            status="PENDING",
            deleted_at__isnull=True
        ).order_by('step_order').first()

        if next_approver_line:
            NotificationService.create_notification(
                sender_id=approval_request.requester.id,
                receiver_id=next_approver_line.approver.id,
                notification_type="LEAVE_APPROVAL_REQUIRED",
                message=f"{approval_request.requester.name}님의 휴가 신청 결재가 필요합니다.",
                notification_type_id=approval_request.id
            )

        return approval_line, leave_request


    @staticmethod
    @transaction.atomic
    def reject_leave_request(
        approval_line_id: int,
        approval_user_id: int,
        comment: str
    ) -> tuple[ApprovalLine, LeaveRequest]:
        """
        결재 라인을 반려합니다.

        :param approval_line_id:
        :param approvaer_user_id:
        :param comment:
        :return:
        """

        # 1. 결재 라인 반려
        approval_line = ApprovalService.reject_approval_line(
            approval_line_id=approval_line_id,
            approval_user_id=approval_user_id,
            comment=comment
        )

        approval_request = approval_line.approval_request

        # 2. LeaveRequest 상태 변경
        leave_request = None
        try:
            leave_request = approval_request.leave_request
            leave_request.status = 'REJECTED'
            leave_request.save(update_fields=['status'])

            # 신청자에게 반려 알림
            NotificationService.create_notification(
                sender_id=approval_user_id,
                receiver_id=approval_request.requester.id,
                notification_type="LEAVE_REJECTED",
                message=f"휴가 신청이 반려되었습니다. 사유: {comment}",
                notification_type_id= leave_request.id
            )

        except LeaveRequest.DoesNotExist:
            pass

        return approval_line, leave_request

    @staticmethod
    @transaction.atomic
    def cancel_leave_request_with_approval(
        approval_request_id: int,
        cancelled_by_user_id: int,
        cancel_reason: str
    ):
        """
        결재 요청과 휴가 신청을 함께 취소합니다.

        비즈니스 규칙:
        - 승인 완료 후 취소 시 LeaveUsage 롤백
        - 반려된 경우는 취소 불가
        :param approval_request_id:
        :param cancelled_by_user_id:
        :param cancel_reason:
        :return:
        """

        # 1. 결재 요청 취소
        approval_request = ApprovalService.cancel_approval_request(
            approval_request_id=approval_request_id,
            cancelled_by_user_id=cancelled_by_user_id
        )

        # 2. 그에 매칭되는 LeaveRequest도 취소
        leave_request = LeaveService.cancel_leave_request(
            approval_request.leave_request.id,
            cancel_reason=cancel_reason,
            cancelled_by_user_id=cancelled_by_user_id
        )

        # 3. 취소 알림 발송
        approvers = ApprovalLine.objects.filter(
            approval_request=approval_request,
            deleted_at__isnull=True
        ).values_list('approver_id', flat=True).distinct()

        # 결재자들에게 취소 알림 발송
        NotificationService.create_bulk_notifications(
            sender_id=cancelled_by_user_id,
            receiver_ids=list(approvers),
            notification_type="LEAVE_CANCELLED",
            message=f"{approval_request.requester.name}님이 휴가 신청을 취소했습니다.",
            notification_type_id=approval_request.id
        )

        return approval_request, leave_request


