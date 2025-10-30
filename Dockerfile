FROM python:3.12-slim

WORKDIR /app

# 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 프로젝트 복사
COPY . .

# 로그 디렉토리 생성
RUN mkdir -p /app/logs

# Gunicorn 실행 (ASGI)
CMD ["gunicorn", "robot_management.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "-w", "4"]

