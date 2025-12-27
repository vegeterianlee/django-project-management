FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 (최소한만 설치)
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# uv 설치 (빠른 Python 패키지 관리자)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Python 경로 설정
ENV PATH="/root/.local/bin:$PATH"

# 의존성 파일 복사
COPY pyproject.toml uv.lock ./

# uv를 사용하여 의존성 설치
# psycopg2-binary가 이미 포함되어 있어 PostgreSQL 연결 가능
RUN uv pip install --system --no-cache .

# 소스 코드 복사
COPY . /app

CMD gunicorn ${GUNICORN_WSGI_APP} --bind ${GUNICORN_BIND} --workers ${GUNICORN_WORKERS}
