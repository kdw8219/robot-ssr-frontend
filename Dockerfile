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

# Websocket --> Daphne로 실행 변경 (ASGI)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "robot_management.asgi:application"]

