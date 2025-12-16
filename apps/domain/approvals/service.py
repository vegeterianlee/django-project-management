"""
Approvals Domain Service

결재 도메인의 비즈니스 로직을 처리하는 서비스입니다.
"""
from typing import Optional, List
from django.db import models
from django.utils import timezone
from apps.domain.approvals.models import ApprovalRequest, ApprovalLine, ApprovalPolicy, ApprovalPolicyStep
from apps.domain.users.models import User, Department, Position
from apps.infrastructure.exceptions.exceptions import ValidationException

class ApprovalService:
    """
    결재 관련 비즈니스 로직을 처리하는 서비스입니다.

    책임:
    - 결재 라인 생성 (ApprovalPolicy 기반)
    - 결재 승인 처리
    - 결재 반려 처리
    - 결재 취소 처리
    """

    @staticmethod
    def _get_ceo_user() -> Optional[User]:
        """
        대표님을 조회합니다.

        Returns:
            User: 대표님 (임원 중 가장 높은 직급)
        """
        ceo_position = Position.objects.filter(
            is_executive=True
        ).order_by('-hierarchy_level').first()

        if ceo_position:
            ceo_user = User.objects.filter(
                position_id=ceo_position.id,
                deleted_at__isnull=True
            ).first()
            return ceo_user

        return None

    @staticmethod
    def _get_department_manager(department: Department) -> Optional[User]:
        """
        부서장을 조회합니다.

        Args:
            department: 부서

        Returns:
            User: 부서장
        """
        return department.get_manager()

    @staticmethod
    def _get_parent_department_manager(department: Department) -> Optional[User]:
        """
        상위 부서의 부서장을 조회합니다.

        Args:
            department: 부서

        Returns:
            User: 상위 부서장
        """
        if department.parent_department:
            return department.parent_department.get_manager()
        return None

    @staticmethod
    def _is_manager(user: User):
        """
        유저가 팀/부서의 장인지 아닌지 확인
        """
        department = Department.objects.filter(
            id=user.department_id
        ).first()

        if not department:
            raise ValidationException('해당 유저의 부서를 찾을 수 없습니다.')

        manager = department.get_manager()
        if not manager:
            raise ValidationException('해당 부서의 부서장을 찾을 수 없습니다.')

        if user.id == department.get_manager().id:
            return True
        else:
            return False


    @staticmethod
    def _resolve_approver(
        approver_selector_type: str,
        user: User,
        department: Optional[Department] = None
    ) -> Optional[User]:
        """
        결재자 선택 타입에 따라 결재자를 결정합니다.

        Args:
            approver_selector_type: 결재자 선택 타입
            user: 신청자
            department: 신청자의 부서 (None이면 조회)

        Returns:
            User: 결재자
        """
        if department is None:
            try:
                department = Department.objects.get(id=user.department_id)
            except Department.DoesNotExist:
                return None

        if approver_selector_type == 'DEPT_MANAGER':
            return ApprovalService._get_department_manager(department)

        elif approver_selector_type == 'PARENT_DEPT_MANAGER':
            return ApprovalService._get_parent_department_manager(department)

        elif approver_selector_type == 'CEO':
            return ApprovalService._get_ceo_user()

        return None


    @staticmethod
    def create_approval_lines(approval_request_id: int) -> List[ApprovalLine]:
        """
        ApprovalPolicy 기반으로 결재 라인을 생성합니다.

        Args:
            approval_request_id: 결재 요청 ID

        Returns:
            List[ApprovalLine]: 생성된 결재 라인 목록

        설계 근거:
        - approval_request_id로 받음: 동시성 이슈 해결
        - ApprovalPolicy 조회: 요청 타입, 부서 타입, 역할에 맞는 정책 조회
        - ApprovalPolicyStep 순서대로 결재자 결정
        - bulk_create로 일괄 생성
        """
        approval_request = ApprovalRequest.objects.select_for_update().get(
            id=approval_request_id,
            deleted_at__isnull=True
        )

        # 이미 결재 라인이 생성되었는 지 확인
        if ApprovalLine.objects.filter(
            approval_request=approval_request,
            deleted_at__isnull=True
        ).exists():
            raise ValidationException('이미 결재 라인이 생성된 요청입니다.')

        requester = approval_request.requester

        # 신청자 부서 조회
        try:
            user_department = Department.objects.get(id=requester.department_id)
        except Department.DoesNotExist:
            raise ValidationException('신청자의 부서 정보를 찾을 수 없습니다.')

        # 팀/부서의 장인지 확인
        leader_flag = ApprovalService._is_manager(requester)
        if leader_flag:
            user_role = "LEADER"
        else:
            user_role = "EMPLOYEE"

        # ApprovalPolicy 조회
        policy = ApprovalPolicy.objects.filter(
            request_type=approval_request.request_type,
            applies_to_dept_type=user_department.organization_type,
            applies_to_role=user_role,
            deleted_at__isnull=True
        ).first()

        if not policy:
            raise ValidationException(f'해당 요청 타입({approval_request.request_type})과 부서 타입({user_department.organization_type})에 대한 결재 정책을 찾을 수 없습니다.')

        policy_steps = ApprovalPolicyStep.objects.filter(
            policy=policy,
            deleted_at__isnull=True
        ).order_by('step_order')

        if not policy_steps:
            raise ValidationException('해당 결재 정책에 대한 결재 단계를 찾을 수 없습니다.')

        # 결재 라인 생성
        approval_lines = []
        for step in policy_steps:
            # 결재자가 누군지 파악
            # 실제 결재자를 맵핑하기 위함
            approver = ApprovalService._resolve_approver(
                step.approver_selector_type,
                requester,
                user_department
            )

            if not approver:
                raise ValidationException(
                    f"결재 단계 {step.step_order}의 결재자를 찾을 수 없습니다. (타입: {step.get_approver_selector_type_display()})")

            approval_line = ApprovalLine(
                approval_request=approval_request,
                step_order=step.step_order,
                approver=approver,
                status='PENDING'
            )
            approval_lines.append(approval_line)

        # bulk_create로 일괄 생성
        if approval_lines:
            ApprovalLine.objects.bulk_create(approval_lines)

            # 첫 번째 결재 라인으로 상태 변경
            approval_request.status = 'IN_PROGRESS'
            approval_request.save(update_fields=['status'])

        return approval_lines


    # 결재자 입장에서 결재 승인
    @staticmethod
    def approve_approval_line(
          approval_line_id: int,
          approver_user_id: int,
          comment: Optional[str] = None
    ) -> ApprovalLine:
        """
        결재 라인을 승인합니다.

        Args:
            approval_line_id: 결재 라인 ID
            approver_user_id: 결재자 사용자 ID
            comment: 결재 의견

        Returns:
            ApprovalLine: 승인된 결재 라인

        설계 근거:
        - approval_line_id로 받음: 동시성 이슈 해결
        - approver_user_id 확인: 결재 권한 검증
        - select_for_update: 비관적 잠금
        - 다음 결재 라인 확인: 순차 결재 처리
        - 모든 결재 완료 시 ApprovalRequest 승인
        """
        approval_line = ApprovalLine.objects.select_for_update().get(
            id=approval_line_id,
            deleted_at__isnull=True
        )

        # 결재 권한 확인
        if approval_line.approver.id != approver_user_id:
            raise ValidationException('결재 권한이 없습니다.')

        # 이미 처리된 결재인지 확인
        if approval_line.status != 'PENDING':
            raise ValidationException(f'이미 처리된 결재입니다. 현재 결재 상태는 {approval_line.get_status_display()} 입니다.')

        approval_request = approval_line.approval_request

        # 현재 결재 라인 승인
        approval_line.status = 'APPROVED'
        approval_line.acted_at = timezone.now()
        if comment:
            approval_line.comment = comment
        approval_line.save(update_fields=['status', 'acted_at', 'comment'])

        # 다음 결재 라인 확인
        next_approval_line = ApprovalLine.objects.filter(
            approval_request=approval_request,
            step_order__gt=approval_line.step_order,
            status='PENDING',
            deleted_at__isnull=True
        ).order_by('step_order').first()

        # 다음 결재 라인이 있으면 다음 결재자가 따로 진행해야하므로 pass
        if next_approval_line:
            pass

        # 최종 결재자인 경우
        else:
            approval_request.status = 'APPROVED'
            approval_request.approved_at = timezone.now()
            approval_request.save(update_fields=['status', 'approved_at'])

        return approval_line

    @staticmethod
    def reject_approval_line(
        approval_line_id: int,
        approval_user_id: int,
        comment: str
    ) -> ApprovalLine:
        """
        결재 라인을 반려합니다.

        Args:
            approval_line_id: 결재 라인 ID
            approval_user_id: 결재자 사용자 ID
            comment: 반려 사유 (필수)

        Returns:
            ApprovalLine: 반려된 결재 라인

        설계 근거:
        - comment 필수: 반려 사유는 필수
        - 반려 시 전체 반려: 비즈니스 규칙
        """

        # 결재 라인 조회
        approval_line = ApprovalLine.objects.select_for_update().get(
            id=approval_line_id,
            deleted_at__isnull=True
        )

        # 결재 권한 확인
        if approval_line.approver_id != approval_user_id:
            raise ValidationException("결재 권한이 없습니다.")

        # 이미 처리된 결재인지 확인
        if approval_line.status != 'PENDING':
            raise ValidationException(f'이미 처리된 결재입니다. 현재 결재 상태는 {approval_line.get_status_display()} 입니다.')

        approval_request = approval_line.approval_request

        # 현재 결재 라인 반려
        approval_line.status = 'REJECTED'
        approval_line.acted_at = timezone.now()
        approval_line.comment = comment
        approval_line.save(update_fields=['status', 'acted_at', 'comment'])

        # 다음 결재 라인 확인안하고 결재 요청을 반려
        approval_request.status = 'REJECTED'
        approval_request.rejected_at = timezone.now()
        approval_request.save(update_fields=['status', 'rejected_at'])

        return approval_line

    @staticmethod
    def cancel_approval_request(
        approval_request_id: int,
        cancelled_by_user_id: int,
    ) -> ApprovalRequest:
        """
        결재 요청을 취소합니다.

        Args:
            approval_request_id: 결재 요청 ID
            cancelled_by_user_id: 취소한 사용자 ID

        Returns:
            ApprovalRequest: 취소된 결재 요청

        설계 근거:
        - 신청자만 취소 가능: 권한 검증
        - 승인/반려된 경우 취소 불가: 비즈니스 규칙
        """

        approval_request = ApprovalRequest.objects.select_for_update().get(
            id=approval_request_id,
            deleted_at__isnull=True
        )

        # 신청자 확인
        if approval_request.requester.id != cancelled_by_user_id:
            raise ValidationException("신청자만 취소할 수 있습니다.")

        # 취소 가능 상태 확인
        if approval_request.status == "CANCELLED":
            raise ValidationException("이미 취소된 결재 요청입니다.")

        # 반려된 결재 요청은 취소불가
        if approval_request.status == 'REJECTED':
            raise ValidationException("반려된 결재 요청은 취소할 수 없습니다.")


        # 결재 취소
        approval_request.cancelled_at = timezone.now()
        approval_request.status = "CANCELLED"
        approval_request.save(update_fields=['status', 'cancelled_at'])
        return approval_request

