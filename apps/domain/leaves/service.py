"""
Leaves Domain Service

휴가 도메인의 비즈니스 로직을 처리하는 서비스입니다.
"""
from datetime import date, timedelta
from decimal import Decimal

import datetime
from django.db import transaction, models
from django.utils import timezone
from apps.domain.leaves.models import LeaveGrant, LeaveRequest, LeaveUsage
from apps.domain.users.models import User
from apps.infrastructure.exceptions.exceptions import ValidationException


class LeaveService:
    """
    휴가 관련 비즈니스 로직을 처리하는 서비스입니다.

    책임:
    - 휴가 신청 생성
    - 휴가 잔액 계산
    - 휴가 사용 처리
    - 휴가 취소 처리
    - 연차 생성 (입사일 기준)
    """

    # 압사년도 기준 직원인 지 확인
    @staticmethod
    def _is_year_based_employee(user: User, target_date: date) -> bool:
        """
        입사년도 기준 직원인지 판정합니다.

        비즈니스 규칙:
        - 입사년도 기준: 매월 입사일 기준으로 연차를 받음
        - 입사일이 없으면 False 반환

        Args:
            user: 사용자

        Returns:
            bool: 입사년도 기준 여부
        """
        if not user.joined_at:
            raise ValidationException("해당 유저의 입사년도가 없습니다.")

        joined_at = user.joined_at
        next_anniversary = date(joined_at.year + 1, joined_at.month, joined_at.day)
        return next_anniversary > target_date

    # 입사년도와 얼만큼 년도 차이나는 지 계산
    @staticmethod
    def _year_diff(user: User, target_date: date) -> int:
        """
        입사년도와 얼만큼 년도 차이나는 지 계산합니다.
        Args:
            user: 사용자

        Returns:
            int: 입사년도와 target_date와의 년수
        """
        if not user.joined_at:
            raise ValidationException("해당 유저의 입사년도가 없습니다.")

        return target_date.year - user.joined_at.year


    # 휴가 신청 생성
    @staticmethod
    def create_leave_request(
        user: User,
        leave_type: str,
        start_date: date,
        end_date: date,
        total_days: Decimal,
        reason: str,
        delegate_user_id: int
    ) -> LeaveRequest:
        """
        휴가 신청을 생성합니다.

        주의: ApprovalRequest 생성은 이 메서드에서 하지 않습니다.
        UseCase에서 LeaveService와 ApprovalService를 조합하여 처리합니다.

        Args:
            user: 신청자
            leave_type: 휴가 타입
            start_date: 시작일
            end_date: 종료일
            total_days: 총 휴가 일수 (사용자가 입력하거나 계산된 값)
            reason: 휴가 사유
            delegate_user_id: 업무 위임 사용자 id

        Returns:
            LeaveRequest: 생성된 휴가 신청

        Raises:
            ValueError: 검증 실패 또는 잔액 부족

        설계 근거:
        - total_days 파라미터: 주말 제외 계산 제거, 사용자 입력 또는 단순 계산
        - 빠른 실패: 검증을 먼저 수행
        - ApprovalRequest 제외: 책임 분리 (UseCase에서 처리)
        """
        # 1. 날짜 순서 검증
        if start_date > end_date:
            raise ValidationException("시작일이 종료일보다 늦을 수 없습니다.")

        # 2. 반차 검증
        if leave_type in ['HALF_MORNING', 'HALF_AFTERNOON']:
            if start_date != end_date:
                raise ValidationException("반차는 하루만 신청 가능합니다.")
            if total_days != Decimal('0.5'):
                raise ValidationException("반차는 0.5일만 신청 가능합니다.")

        # 2. total_days 검증
        if total_days <= 0:
            raise ValidationException("휴가 일수는 0보다 커야 합니다.")

        # 3. 잔액 확인
        remaining = LeaveService.get_leave_remaining(user)
        if remaining < total_days:
            raise ValidationException(f"잔여 휴가 일수가 부족합니다. 잔여 휴가일: {remaining}일, 휴가 요청일: {total_days}일")

        # 4. LeaveRequest 생성
        leave_request = LeaveRequest.objects.create(
            user=user,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            delegate_user_id=delegate_user_id,
            total_days=total_days,
            status='PENDING'
        )

        return leave_request

    # 휴가 잔액 계산
    @staticmethod
    def get_leave_remaining(user: User, as_of_date: date = None) -> Decimal:
        """
        사용자의 휴가 잔액을 계산합니다.

        Args:
            user: 사용자
            leave_type: 휴가 타입

        Returns:
            Decimal: 사용 가능한 휴가 일수

        설계 근거:
        - as_of_date 파라미터: 만료일 체크를 위한 기준일
        - aggregate(Sum()): DB 레벨에서 집계하여 효율적 처리
        - deleted_at__isnull=True: 소프트 삭제된 레코드 제외
        - expires_at 체크: 만료된 휴가는 제외
        """
        if as_of_date is None:
            as_of_date = date.today()

        queryset = LeaveGrant.objects.filter(
            user=user,
            deleted_at__isnull=True,
        ).filter(
            models.Q(expires_at__gt=as_of_date)
        )

        total_remaining = queryset.aggregate(
            total=models.Sum('remaining_days')
        )['total']

        return total_remaining


    # 휴가 사용 처리
    @staticmethod
    def create_leave_usage(leave_request_id: int) -> list[LeaveUsage]:
        """
        승인된 휴가 신청에 대해 휴가 사용을 생성합니다.

        Args:
            leave_request: 승인된 휴가 신청

        Returns:
            list[LeaveUsage]: 생성된 휴가 사용 목록

        Raises:
            ValueError: 휴가 잔액 부족 또는 승인되지 않은 신청

        설계 근거:
        - 승인 상태 확인: 비즈니스 규칙
        - 중복 사용 방지: 이미 사용 처리된 신청 체크
        - FIFO 방식: granted_at 오름차순으로 먼저 지급된 것부터 사용
        - 여러 LeaveUsage 생성: 여러 LeaveGrant에서 차감 가능
        """
        # 1. 승인 상태 확인
        leave_request = LeaveRequest.objects.select_for_update().get(
            id=leave_request_id,
            deleted_at__isnull=True
        )

        if leave_request.status != 'APPROVED':
            raise ValidationException("승인된 휴가 신청만 사용 처리가능합니다.")

        # 2. 이미 사용처리되었는 지 확인
        if LeaveUsage.objects.filter(
            leave_request=leave_request,
            deleted_at__isnull=True
        ).exists():
            raise ValidationException("이미 사용 처리된 휴가 신청입니다.")

        usage_records = []
        grants_to_update = []

        if leave_request.leave_type in ['HALF_MORNING', 'HALF_AFTERNOON']:
            # 3. 사용 가능한 LeaveGrant 조회, FIFO 식
            available_grants = LeaveGrant.objects.select_for_update().filter(
                user=leave_request.user,
                grant_type__in=['ANNUAL'],
                remaining_days__gt=0,
                deleted_at__isnull=True
            ).order_by('granted_at')

            if not available_grants.exists():
                raise ValidationException("사용 가능한 연차가 없습니다.")

            grant = available_grants.first()
            if grant.remaining_days < Decimal('0.5'):
                raise ValidationException("반차 사용을 위한 남은 휴가 수가 부족합니다.")

            usage = LeaveUsage.objects.create(
                user=leave_request.user,
                leave_grant=grant,
                leave_request=leave_request,
                used_days=Decimal('0.5'),
                used_at=leave_request.start_date
            )
            usage_records.append(usage)

            grant.remaining_days -= Decimal('0.5')
            if grant.remaining_days == 0:
                grant.deleted_at = timezone.now()

            grants_to_update.append(grant)

        # 연차 처리
        else:
            available_grants = LeaveGrant.objects.select_for_update().filter(
                user=leave_request.user,
                grant_type=leave_request.leave_type,
                remaining_days__gt=0,
                deleted_at__isnull=True
            ).order_by('granted_at')

            remaining_to_use = leave_request.total_days
            current_date = leave_request.start_date

            # 사용 가능한 LeaveGrant 찾기
            for grant in available_grants:
                # 하루 사용량 (월차로 들어오는 연차 기준)
                daily_use = min(remaining_to_use, grant.remaining_days)

                usage = LeaveUsage.objects.create(
                    user=leave_request.user,
                    leave_grant=grant,
                    leave_request=leave_request,
                    used_days=daily_use,
                    used_date=current_date
                )
                usage_records.append(usage)

                grant.remaining_days -= daily_use
                if grant.remaining_days == 0:
                    grant.deleted_at = timezone.now()

                grants_to_update.append(grant)
                remaining_to_use -= daily_use
                current_date += timedelta(days=daily_use)

            if remaining_to_use > 0:
                raise ValidationException(f"잔여 휴가 일수가 부족합니다. 부족한 일수: {remaining_to_use}일")

        # bulk로 생성 및 업데이트
        if usage_records:
            LeaveUsage.objects.bulk_create(usage_records)

        if grants_to_update:
            LeaveGrant.objects.bulk_update(
                grants_to_update,
                ['remaining_days', 'deleted_at']
            )

        return usage_records

    # 입사일 기준으로 연차 생성
    @staticmethod
    def create_annual_leave_grant(user: User, target_date: date) -> list[LeaveGrant]:
        """
        입사일 기준으로 연차를 생성합니다.
        """
        if not user.joined_at:
            raise ValidationException("입사일이 없는 사용자는 연차를 생성할 수 없습니다.")

        is_year_based = LeaveService._is_year_based_employee(user, target_date)
        joined_at = user.joined_at
        grants = []

        # 입사년도일 때는
        if is_year_based:
            # 매월 1일인 경우: 월차 생성 (1일)
            if target_date.day == 1:
                second_next_anniversary = date(joined_at.year+2, joined_at.month, joined_at.day)
                expires_at = second_next_anniversary - timedelta(days=1)
                grant = LeaveGrant.objects.create(
                    user=user,
                    grant_type='ANNUAL',
                    total_days=Decimal('1.0'),
                    remaining_days=Decimal('1.0'),
                    granted_at=timezone.now(),
                    expires_at=expires_at
                )
                grants.append(grant)

        # 딱 1년 이후가 되어 연차 생성이 된 경우
        else:
            if target_date.month == joined_at.month and target_date.day == joined_at.day:
                # 근속연수 계산
                years_of_visit = LeaveService._year_diff(user, target_date)

                # 기본 연차 15개 + 근속년수에 따른 추가 (2년 주기로 1개 증가)
                additional_leaves = years_of_visit // 2
                total_annual_leaves = Decimal('15') + Decimal(str(additional_leaves))

                # 다음 입사 기념일 계산: target_date의 다음 해 입사일
                next_anniversary = date(target_date.year + 1, joined_at.month, joined_at.day)

                # 만료일: 다음 입사 기념일 전날
                expires_at = next_anniversary - timedelta(days=1)

                grant = LeaveGrant.objects.create(
                    user=user,
                    grant_type='ANNUAL',
                    total_days=total_annual_leaves,
                    remaining_days=total_annual_leaves,
                    granted_at=timezone.now(),
                    expires_at=expires_at
                )
                grants.append(grant)

        return grants


    # 휴가 취소 처리
    @staticmethod
    def cancel_leave_request(
        leave_request_id: int,
        cancel_reason: str,
        cancelled_by_user_id: int
    ) -> LeaveRequest:
        """
        휴가 신청을 취소합니다.

        Args:
            leave_request: 취소할 휴가 신청
            cancel_reason: 취소 사유
            cancelled_by: 취소한 사용자

        Returns:
            LeaveRequest: 취소된 휴가 신청

        Raises:
            ValueError: 취소할 수 없는 상태

        설계 근거:
        - 상태 확인: 취소 가능 여부 검증
        - 승인된 경우: 사용 처리 여부 확인 필요
        - 취소 일시 저장: timezone.now() 사용
        """

        # 1. 취소 가능 상태 확인
        leave_request = LeaveRequest.objects.select_for_update().get(
            id=leave_request_id,
            deleted_at__isnull=True
        )
        # 취소 가능 상태 확인
        if leave_request.status == 'CANCELLED':
            raise ValidationException("이미 취소된 휴가 신청입니다.")

        # 승인된 경우에는 이전 상태로 롤백해야됨
        if leave_request.status != 'APPROVED':
            # 승인된 경우, 이미 사용 처리되었는 지 확인
            if LeaveUsage.objects.filter(
                leave_request=leave_request,
                deleted_at__isnull=True
            ).exists():
                LeaveService.rollback_leave_usage(leave_request_id=leave_request_id)

        # 2. 상태 변경
        leave_request.status = 'CANCELLED'
        leave_request.cancelled_at = timezone.now()
        leave_request.cancel_reason = cancel_reason
        leave_request.save(update_fields=['status', 'cancelled_at', 'cancel_reason'])

        return leave_request

    @staticmethod
    def rollback_leave_usage(leave_request_id: int) -> None:
        """
        휴가 사용 처리를 롤백합니다.

        설계 근거:
        - 별도 메서드로 분리: 단일 책임 원칙
        - UseCase에서 호출: 복잡한 로직은 UseCase에서 조합
        """
        # LeaveUsage 조회
        usages = LeaveUsage.objects.filter(
            leave_request_id=leave_request_id,
            deleted_at__isnull=True
        ).select_related('leave_grant')

        # 각 LeaveGrant에 반환
        grants_to_update = []
        for usage in usages:
            grant = usage.leave_grant
            grant.remaining_days += usage.used_days

            # 잔액이 0보다 커지면 삭제 조치 해제
            if grant.remaining_days > 0 and grant.deleted_at is not None:
                grant.deleted_at = None

            grants_to_update.append(grant)

        if grants_to_update:
            LeaveGrant.objects.bulk_update(
                grants_to_update,
                ["remaining_days", "deleted_at"]
            )

        # LeaveUsage 소프트 삭제
        usages.delete()