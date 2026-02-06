# 1. 가벼운 파이썬 이미지 사용
FROM python:3.9-slim

# 2. 작업 폴더 설정
WORKDIR /app

# 3. 라이브러리 설치 (캐싱을 위해 먼저 복사)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 소스 코드 복사
COPY . .

# 5. 실행 명령 (Cloud Run은 8080 포트를 좋아합니다)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]