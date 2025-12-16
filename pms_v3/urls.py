"""
URL configuration for pms_v3 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("api/admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    # API 엔드포인트
    # Company 도메인 API
    path("api/", include("apps.presentation.api.company.urls")),

    # Users 도메인 API
    path("api/", include("apps.presentation.api.users.urls")),

    # Projects 도메인 API
    path("api/", include("apps.presentation.api.projects.urls")),

    # Tasks 도메인 API
    path("api/", include("apps.presentation.api.tasks.urls")),

    # Meetings 도메인 API
    path("api/", include("apps.presentation.api.meetings.urls")),

    # Sales 도메인 API
    path("api/", include("apps.presentation.api.sales.urls")),

    # Designs 도메인 API
    path("api/", include("apps.presentation.api.designs.urls")),

    # Leaves 도메인 API
    path("api/", include("apps.presentation.api.leaves.urls")),

    # Approvals 도메인 API
    path("api/", include("apps.presentation.api.approvals.urls")),

    # Notifications 도메인 API
    path("api/", include("apps.presentation.api.notifications.urls"))

]
