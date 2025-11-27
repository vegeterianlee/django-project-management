"""
Projects URLs

Projects 도메인의 URL 라우팅을 정의합니다.
DRF Router를 사용하여 ViewSet을 자동으로 URL에 등록합니다.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.presentation.controllers.projects.views import (
    ProjectViewSet,
    ProjectCompanyLinkViewSet,
    ProjectAssigneeViewSet,
)

# DRF Router 생성
# DefaultRouter는 표준 RESTful URL 패턴을 자동으로 생성합니다
router = DefaultRouter()

# ViewSet 등록
# router.register(prefix, viewset, basename)
# prefix: URL 접두사
# viewset: 등록할 ViewSet 클래스
# basename: URL 이름의 기본 이름 (선택사항)
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'project-company-links', ProjectCompanyLinkViewSet, basename='project-company-link')
router.register(r'project-assignees', ProjectAssigneeViewSet, basename='project-assignee')

# URL 패턴 정의
# router.urls에는 자동으로 생성된 URL 패턴들이 포함됩니다
urlpatterns = [
    path('', include(router.urls)),
]

# 자동 생성되는 URL 패턴:
# GET    /api/projects/                              → ProjectViewSet.list()
# POST   /api/projects/                              → ProjectViewSet.create()
# GET    /api/projects/{id}/                          → ProjectViewSet.retrieve()
# PUT    /api/projects/{id}/                          → ProjectViewSet.update()
# PATCH  /api/projects/{id}/                          → ProjectViewSet.partial_update()
# DELETE /api/projects/{id}/                         → ProjectViewSet.destroy()
# GET    /api/projects/by-status/{status}/            → ProjectViewSet.by_status() (@action)
# GET    /api/projects/by-code/{project_code}/        → ProjectViewSet.by_code() (@action)
# GET    /api/projects/by-company/{company_id}/       → ProjectViewSet.by_company() (@action)
# GET    /api/projects/by-assignee/{user_id}/         → ProjectViewSet.by_assignee() (@action)
# GET    /api/projects/active/                        → ProjectViewSet.active() (@action)
