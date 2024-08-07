# FastApi-Post

## Introduce
간단한 게시판 작성 프로젝트입니다.

## Pre-Require
* Python 3.11.9
* poetry

## Installation
가상환경 설정
```
poetry install
```

가상환경 실행
```
poetry shell
```
## Start
서버 실행
```
Dev: uvicorn main:app --reload
Prod: uvicorn main:app
```

## API
API 예시
```
POST /posts - 포스트 생성
GET /posts?page=1 - 전체 포스트 리스트
GET /posts/{post_id} - post_id 포스트

POST /users/login - 로그인
```

API 상세
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
        int author_id FK "작성자 ID"
        int content_id FK "포스트 내용 ID"
        datetime created_at "포스트 생성일자"
        datetime updated_at "포스트 갱신일자"
    }

    POST ||--|| POSTCONTENT:""
    POSTCONTENT {
        int id PK "포스트 ID"
        str content "포스트 내용"
        datetime created_at "포스트 내용 생성일자"
        datetime updated_at "포스트 내용 갱신일자"
    }
    
    USER ||--o{ POST: ""
    USER ||--o{ COMMENT: ""
    USER {
        int id PK "유저 ID"
        str nickname "유저닉네임"
        str password "유저 비밀번호"
        datetime created_at "포스트 생성일자"
        datetime updated_at "포스트 갱신일자"
    }

    COMMENT {
        int id PK "코멘트 ID"
        str content "코멘트 내용"
        int author_id FK "작성자 ID"
        int post_id FK "포스트 ID"
        datetime created_at "코멘트 생성일자"
        datetime updated_at "코멘트 갱신일자"
    }
```

## TEST
### E2E Test
```
pytest
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
