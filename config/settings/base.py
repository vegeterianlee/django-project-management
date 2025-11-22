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

env_file = BASE_DIR / ".envs" / f".{ENVIRONMENT}"

if env_file.exists():
    env.read_env(env_file)     # <--- Read .env file into os.environ


# -----------------------------
# Core Django settings
# -----------------------------
SECRET_KEY = env("DJANGO_SECRET_KEY")

DEBUG = env.bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost"])


# -----------------------------
# Database
# -----------------------------
DATABASES = {
    "default": env.db("DATABASE_URL")
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True


# -----------------------------
# Apps
# -----------------------------
INSTALLED_APPS = [
    "polls.apps.PollsConfig",
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
    "daesan_pms.users",
]

INSTALLED_APPS += THIRD_PARTY_APPS + LOCAL_APPS


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


STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"