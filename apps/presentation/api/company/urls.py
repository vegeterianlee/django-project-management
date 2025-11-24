"""
Company URLs

Company 도메인의 URL 라우팅을 정의합니다.
DRF Router를 사용하여 ViewSet을 자동으로 URL에 등록합니다.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.presentation.controllers.company.views import CompanyViewSet, ContactPersonViewSet

# DRF Router 생성
# DefaultRouter는 표준 RESTful URL 패턴을 자동으로 생성합니다
router = DefaultRouter()

# ViewSet 등록
# router.register(prefix, viewset, basename)
# prefix: URL 접두사
# viewset: 등록할 ViewSet 클래스
# basename: URL 이름의 기본 이름 (선택사항)
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'contact-persons', ContactPersonViewSet, basename='contact-person')

# URL 패턴 정의
# router.urls에는 자동으로 생성된 URL 패턴들이 포함됩니다
urlpatterns = [
    path('', include(router.urls)),
]

# 자동 생성되는 URL 패턴:
# GET    /api/company/companies/                    → CompanyViewSet.list()
# POST   /api/company/companies/                    → CompanyViewSet.create()
# GET    /api/company/companies/{id}/               → CompanyViewSet.retrieve()
# PUT    /api/company/companies/{id}/               → CompanyViewSet.update()
# PATCH  /api/company/companies/{id}/               → CompanyViewSet.partial_update()
# DELETE /api/company/companies/{id}/              → CompanyViewSet.destroy()
# GET    /api/company/companies/by-type/{type}/    → CompanyViewSet.by_type() (@action)