# FastApi-Post

## Introduce
간단한 게시판 작성 프로젝트입니다.

## Pre-Require
* Python 3.11.9
* poetry

## Installation
저장소 복사
```
git clone https://github.com/f-lab-edu/fastapi-post.git
```

가상환경 설정
```
poetry install
```

가상환경 실행
```
poetry shell
```

## Start
* 앱 이미지 생성
```
docker build --tag fastapi-post:latest
```
* docker-compose 실행
```
docker-compose up -d
```
* docker-compose 종료
```
docker-compose down
```
## Development
* MySQL 다운로드
```
docker pull mysql:lts
```

* MySQL 실행
```
docker run -d --name mysql -p 3306:3306 -e MYSQL_DATABASE=exampledb -e MYSQL_USER=user -e MYSQL_PASSWORD=password -e MYSQL_ROOT_PASSWORD=root mysql:lts
```

* Redis 다운로드
```
docker pull Redis:alpine
```

* Redis 실행
```
docker run -d --name redis -p 6379:6379 redis:alpine
```
* 환경변수 설정
```
export PYTHONPATH="./"
export DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/exampledb
export REDIS_URL=redis://localhost
```
OR
* .env
```
PYTHONPATH="./"
DATABASE_URL="mysql+aiomysql://user:password@127.0.0.1:3306/exampledb"
REDIS_URL="redis://localhost"
```

* 서버 실행
```
uvicorn src.main:app --host localhost --port 8000
```

## API
API 예시
* 포스트 생성
```
curl -X POST http://localhost:8000/posts \
     -H "Content-Type: application/json" \
     -d '{"title": "제목", "content": "내용"}'
```
* 전체 포스트 리스트
```
curl -X GET "http://localhost:8000/posts?page=1"
```
* post_id 포스트
```
curl -X GET http://localhost:8000/posts/1
```
* 로그인
```
curl -X POST http://localhost:8000/users/login \
     -H "Content-Type: application/json" \
     -d '{"username": "사용자이름", "password": "비밀번호"}'
```

* API 상세
```
http://localhost:8000/docs
```

## ERD
* mermaid.js
```mermaid
erDiagram
    POST ||--o{ COMMENT:""
    POST {
        int id PK "포스트 ID"
        str title "포스트 제목"
        str content "포스트 내용"
        int author_id FK "작성자 ID"
        int post_view_id FK "조회수 ID"
        datetime created_at "포스트 생성일자"
        datetime updated_at "포스트 갱신일자"
    }

    POST ||--|| POSTVIEW:""
    POSTVIEW {
        int id PK "조회수 ID"
        int count "조회수"
    }

    USER ||--o{ POST: ""
    USER ||--o{ COMMENT: ""
    USER {
        int id PK "유저 ID"
        str nickname "유저닉네임"
        str password "유저 비밀번호"
        str role "유저 타입"
        str profile_img_url "유저 프로필 이미지 주소"
        datetime created_at "포스트 생성일자"
        datetime updated_at "포스트 갱신일자"
    }

    USER ||--|| LOGINSESSION: ""
    LOGINSESSION {
        int id PK "세션 ID"
        str session_data "세션 값"
        datetime created_at "세션 생성일자"
    }

    COMMENT {
        int id PK "코멘트 ID"
        str content "코멘트 내용"
        int author_id FK "작성자 ID"
        int post_id FK "포스트 ID"
        datetime created_at "코멘트 생성일자"
        datetime updated_at "코멘트 갱신일자"
    }

    USER ||--o{ LIKE: ""
    POST ||--o{ LIKE: ""
    LIKE {
        int id PK "좋아요 ID"
        datetime created_at "좋아요 생성일자"
        int user_id FK "유저 ID"
        int post_id FK "포스트 ID"
    }

    USER ||--o{ NOTIFICATION: ""
    POST ||--o{ NOTIFICATION: ""
    NOTIFICATION {
        int id PK "알림 ID"
        datetime created_at "알림 생성일자"
        int user_id FK "좋아요 한 유저 ID"
        int post_id FK "좋아요 한 포스트 ID"
    }
```

## TEST
### E2E Test
* E2E Test start
```
pytest tests/e2e
```
* Unit Test
```
pytest tests/unit
```
### Test Coverage
```

Name                            Stmts   Miss  Cover
---------------------------------------------------
main.py                            12      1    92%
src\API\comment.py                 49     20    59%
src\API\post.py                    58     26    55%
src\API\user.py                    31     14    55%
src\auth.py                        31      1    97%
src\database.py                    18      0   100%
src\domain\comment.py              13      0   100%
src\domain\post.py                 31      0   100%
src\domain\user.py                 15      0   100%
src\schemas\comment.py             23      0   100%
src\schemas\post.py                23      0   100%
src\schemas\user.py                22      0   100%
src\service\comment.py             38      8    79%
src\service\post.py                47     16    66%
src\service\user.py                20      4    80%
tests\e2e\test_comment_e2e.py     109      0   100%
tests\e2e\test_post_e2e.py        107      0   100%
tests\e2e\test_user_e2e.py         65      0   100%
---------------------------------------------------
TOTAL                             712     90    87%
```

## Locust
```
locust -f locust-test\stress_test.py
```
* workers = 1 부하테스트 결과
```
locust-test\report_worker_1.html
```
* workers = 5 부하테스트 결과
```
locust-test\report_worker_5.html
```