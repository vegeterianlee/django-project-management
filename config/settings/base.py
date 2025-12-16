"""
Django settings for pms_v3 project.
"""

import os
from pathlib import Path
import environ

# -----------------------------
# Base directory setup
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# -----------------------------
# Environment selection
# -----------------------------
ENVIRONMENT = os.environ.get("DJANGO_ENV", "local")

# -----------------------------
# Load environment variables
# -----------------------------
env = environ.Env()   # <--- Core django-environ object

env_file = BASE_DIR / ".env"

if env_file.exists():
    env.read_env(env_file)     # <--- Read .env file into os.environ


# -----------------------------
# Core Django settings
# -----------------------------
SECRET_KEY = env("DJANGO_SECRET_KEY")

DEBUG = env.bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = ["*"]


# -----------------------------
# Database
# -----------------------------
DATABASES = {
    "default": env.db("DATABASE_URL"),
}

DATABASES["default"]["OPTIONS"] = {
    "charset": "utf8mb4",
    "init_command": "SET sql_mode='STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'",
    "use_unicode": True,
}

DATABASES["default"]["CONN_MAX_AGE"] = 600
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -----------------------------
# Apps
# -----------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "django_celery_beat",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
]

LOCAL_APPS = [
    # Infrastructure 레이어 (공통 모델)
    'apps.infrastructure.time_stamp',
    'apps.infrastructure.outbox',

    # Domain 레이어 앱들
    'apps.domain.company',
    'apps.domain.users',
    'apps.domain.projects',
    'apps.domain.tasks',
    "apps.domain.meetings",
    "apps.domain.sales",
    "apps.domain.designs",
    "apps.domain.leaves",
    "apps.domain.notifications",
    "apps.domain.approvals",
]

INSTALLED_APPS += THIRD_PARTY_APPS + LOCAL_APPS
ROOT_URLCONF = "pms_v3.urls"


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates']
        ,
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

STATIC_URL = "static/"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "PMS API",
    "DESCRIPTION": "Project Management Service API",
    "VERSION": "0.2.0",
    "DISABLE_ERRORS_AND_WARNINGS": False,
    "ENUM_NAME_OVERRIDES": {
            "ProjectCompanyLink.ROLE_CHOICES": "ProjectRoleEnum",
            "Company.COMPANY_TYPES": "CompanyTypeEnum",
            "ProjectMethod.METHOD_CHOICES": "ProjectMethodEnum",
            "Task.STATUS_CHOICES": "TaskStatusEnum",
            "Task.PRIORITY_CHOICES": "TaskPriorityEnum",
            "Task.PHASE_CHOICES": "TaskPhaseEnum",
            "Project.STATUS_CHOICES": "ProjectStatusEnum",
            "DesignVersion.STATUS_CHOICES": "DesignVersionStatusEnum",
            "ProjectSales.SALES_TYPE_CHOICES": "ProjectSalesTypeEnum",
        },
}
# -----------------------------
# Redis Cache
# -----------------------------
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv("CACHE_REDIS_URL")
    }
}

JWT_REDIS_URL = os.getenv("JWT_REDIS_URL")

# -----------------------------
# Celery
# -----------------------------
CELERY_BROKER_URL = env(
    "CELERY_BROKER_URL",
    default="redis://redis:6379/0"
)
CELERY_RESULT_BACKEND = env(
    "CELERY_RESULT_BACKEND",
    default="redis://redis:6379/1"
)

CELERY_TASK_ALWAYS_EAGER = False


# -----------------------------
# Django Misc
# -----------------------------
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = False


