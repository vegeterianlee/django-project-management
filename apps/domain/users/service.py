"""
Users Domain Service

사용자 관련 비즈니스 로직을 처리하는 서비스입니다.
"""
from django.db import transaction
from django.utils import timezone
from apps.domain.users.models import User, Department, DepartmentManager
from apps.infrastructure.exceptions.exceptions import ValidationException
from apps.infrastructure.serializers.users import UserModelSerializer


class UserService:
    """
    사용자 관련 비즈니스 로직을 처리하는 서비스

    책임:
    - 부서장 임명
    - 부서장 해제
    - 부서장 조회
    """

    @staticmethod
    @transaction.atomic
    def assign_department_manager(department_id: int, user_id: int) -> DepartmentManager:
        """
        특정 사용자를 부서장으로 임명합니다.

        Args:
            department_id: 부서 ID
            user_id: 사용자 ID

        :param department_id:
        :param user_id:
        :return:
        """
        try:
            # 부서 확인
            department = Department.objects.get(id=department_id)
            existing_manager = DepartmentManager.objects.filter(
                department=department,
                deleted_at__isnull=True
            ).first()

            if existing_manager:
                raise ValidationException(
                    f"부서{department.name}에 이미 부서장 ({existing_manager.user.name})님이 존재합니다."
                )

            # 사용자 존재 확인
            user = User.objects.get(id=user_id, deleted_at__isnull=True)
            if not user:
                raise ValidationException(f"사용자가 존재하지 않습니다.")

            # 사용자가 해당 부서에 속하는 지 확인
            if user.department_id != department_id:
                raise ValidationException(f"해당 사용자는 {department.name}에 속해 있지 않습니다.")

            # 부서장 생성
            department_manager = DepartmentManager.objects.create(
                department=department,
                user_id=user_id
            )
            return department_manager

        except Department.DoesNotExist:
            raise ValidationException(f"부서가 존재하지 않습니다.")


    @staticmethod
    @transaction.atomic
    def remove_department_manager(department_id: int) -> bool:
        """
        부서장을 해제합니다.

        Args:
            department_id: 부서 ID

        Returns:
            bool: 해제 성공 여부

        Raises:
            ValidationException: 부서 없음 또는 부서장 없음
        """

        try:
            department = Department.objects.get(id=department_id)
        except Department.DoesNotExist:
            raise ValidationException(f"부서(ID: {department_id})를 찾을 수 없습니다.")

        # 현재 부서장 확인
        current_manager = DepartmentManager.objects.filter(
            department=department,
            deleted_at__isnull=True
        ).first()

        if not current_manager:
            raise ValidationException(f"해당 부서에 부서장이 없습니다.")

        # 부서장 소프트 삭제
        current_manager.deleted_at = timezone.now()
        current_manager.save(update_fields=['deleted_at'])
        return True

    @staticmethod
    def get_department_manager(department_id: int) -> User:
        """
        부서장을 조회합니다.

        Args:
            department_id: 부서 ID

        Returns:
            User: 부서장 사용자 객체 (없으면 None)

        Raises:
            ValidationException: 부서를 찾을 수 없을 때
        """
        try:
            department = Department.objects.get(id=department_id)
        except Department.DoesNotExist:
            raise ValidationException(f"부서(ID: {department_id})를 찾을 수 없습니다.")

        manager = department.get_manager()
        return manager


    @staticmethod
    @transaction.atomic
    def bulk_create_users(validated_users: list) -> list:
        """
        user 다수 생성합니다.
        :param validated_users:
        :return:
        """

        users_to_create = []
        passwords = {}
        user_uids = []

        # set_password가 User 객체를 통해서 가능함
        for user_data in validated_users:
            password = user_data.pop('password')

            # User 객체 생성
            user = User(**user_data)
            users_to_create.append(user)

            # 비밀번호 저장
            passwords[user.user_uid] = password
            user_uids.append(user.user_uid)

        # buik create 수행
        created_users = User.objects.bulk_create(
            users_to_create,
            ignore_conflicts=False  # 중복 시 에러 발생
        )

        # pk가 채워졌는 지 확인
        users_with_pk = User.objects.filter(user_uid__in=user_uids)
        user_dict = {user.user_uid: user for user in users_with_pk}

        # 각 유저의 비밀번호 설정
        for user in users_with_pk:
            user.set_password(passwords[user.user_uid])
            user.save()

        # 생성된 유저 정보 반환
        return list(user_dict.values())

