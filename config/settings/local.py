"""
Local Development Settings

로컬 개발 환경에서 사용되는 설정을 정의합니다.
base.py의 모든 설정을 상속받고, 개발 환경에 특화된 설정만 오버라이드합니다.
"""
from .base import *

# 개발 환경임을 명시
ENVIRONMENT = "local"