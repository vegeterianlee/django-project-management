"""
Project Creation UseCase

프로젝트 생성 시 관련 엔티티(ProjectSales, ProjectDesign)를 함께 생성하는 유즈케이스입니다.
"""
from typing import Dict, Any, Optional
from django.db import transaction
from apps.domain.projects.models import Project, ProjectMethod
from apps.domain.sales.models import ProjectSales
from apps.domain.designs.models import ProjectDesign
from apps.infrastructure.exceptions.exceptions import ValidationException
from apps.infrastructure.outbox.services import OutboxService


class ProjectCreationUseCase:
    """
    프로젝트 생성 관련 유즈케이스입니다.

    책임:
    - 프로젝트 생성
    - Outbox 이벤트를 통해 ProjectSales와 ProjectDesign 생성 (비동기)
    - 트랜잭션으로 데이터 일관성 보장
    """

    @staticmethod
    @transaction.atomic
    def create_project_with_sales_and_design(
        project_validated_data: Dict[str, Any],
        sales_validated_data: Optional[Dict[str, Any]] = None,
        design_validated_data: Optional[Dict[str, Any]] = None,
        methods_data: Optional[list] = None,
    ):
        """
        프로젝트와 함께 ProjectSales와 ProjectDesign을 생성합니다.

        설계 근거:
        - Project는 즉시 생성
        - ProjectSales와 ProjectDesign은 Outbox 이벤트를 통해 비동기 생성
        - 트랜잭션 커밋 후 Celery 태스크가 실행되어 관련 엔티티 생성
        - 실패 시 재시도 메커니즘 제공

        Args:
            project_validated_data: ProjectModelSerializer의 validated_data
            sales_validated_data: ProjectSalesModelSerializer의 validated_data (선택사항)
            design_validated_data: ProjectDesignModelSerializer의 validated_data (선택사항)
            methods_data: 공법 리스트 (선택사항)

        Returns:
            tuple[Project, ProjectSales, ProjectDesign]: 생성된 프로젝트, 영업 정보, 설계 정보
        """

        # project data
        project_data = {
            k: v for k, v in project_validated_data.items()
            if k != 'methods_input'
        }

        project = Project.objects.create(**project_data)

        # 2. ProjectMethod 생성
        if methods_data:
            project_methods = [
                ProjectMethod(project=project, method=method)
                for method in methods_data
            ]
            ProjectMethod.objects.bulk_create(project_methods)

        # 3. Sales, Design 생성 -> outbox 이벤트로 발행
        sales_data_for_event = {
            k: v for k, v in sales_validated_data.items()
            if k != 'project' and v is not None
        }

        design_data_for_event = {
            k: v for k, v in design_validated_data.items()
            if k != 'project' and v is not None
        }

        # Outbox 이벤트 생성
        OutboxService.create_project_creation_event(
            project_id=project.id,
            sales_data=sales_data_for_event if sales_data_for_event else None,
            design_data=design_data_for_event if design_data_for_event else None,
        )


        return project