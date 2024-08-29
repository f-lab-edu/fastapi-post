# 베이스 이미지로 Python 3.11.9 사용
FROM python:3.11.9-slim

# 작업 디렉토리 설정
WORKDIR /

# Poetry 설치
RUN pip install poetry

WORKDIR /root/fastapi-post

# 프로젝트 파일 복사
COPY . .

# Poetry 설정: 가상 환경을 생성하지 않도록 설정
RUN poetry config virtualenvs.create false

# 의존성 설치
RUN poetry install --no-root

# 포트 8000 노출
EXPOSE 8000

# 앱 실행
CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
