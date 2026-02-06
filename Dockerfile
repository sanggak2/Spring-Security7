# 1. 파이썬 3.10 slim (가볍고 안정적)
FROM python:3.10-slim

# 2. 작업 폴더
WORKDIR /app

# 3. 필수 시스템 패키지 (빌드 도구)
# --no-install-recommends로 불필요한 패키지 설치 방지 (이미지 크기 최소화)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. 의존성 파일 복사
COPY requirements.txt .

# 🔥 [핵심 전략: CPU Torch 선점 설치 + 버전 고정]
# requirements.txt에 torch가 없으므로 여기서 먼저 설치하여 GPU 버전을 방지함.
# 운영 안정성을 위해 버전을 명시(Pinning)합니다.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 5. 나머지 라이브러리 설치
# requirements.txt에는 sentence-transformers==2.3.1 등이 명시되어 있어야 함
RUN pip install --no-cache-dir -r requirements.txt

# 6. 소스 코드 복사
COPY . .

# 7. 실행 (Cloud Run 기본 포트 8080)
ENV PORT=8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]