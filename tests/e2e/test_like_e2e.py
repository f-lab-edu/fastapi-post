from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth import hash_password
from src.config import config
from src.database import get_session
from src.domains.like import Like
from src.domains.post import Post
from src.domains.user import User
from src.main import app

DATABASE_URL = config.DATABASE_URL


@pytest_asyncio.fixture
async def test_client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield test_session

    app.dependency_overrides[get_session] = override_get_session
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")  # type: ignore
    hashed_password = hash_password(plain_password="Test_password")
    new_user = User(nickname="test_user", password=hashed_password)
    test_session.add(new_user)
    await test_session.commit()

    yield client

    app.dependency_overrides.clear()


# 포스트에 좋아요 추가
@pytest.mark.asyncio
@pytest.mark.create
async def test_create_like_ok(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # given
    user_result = await test_session.exec(
        select(User).where(User.nickname == "test_user")
    )
    user = user_result.first()
    test_session.add(
        Post(author_id=user.id, title="test_title_1", content="test_content_1")  # type: ignore
    )
    await test_session.commit()
    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )

    # when
    response = await test_client.post(
        "/likes/",
        json={
            "post_id": 1,
        },
    )

    # then
    assert response.status_code == 201
    assert response.json()["post_id"] == 1
    assert response.json()["user_id"] == 1

    result = await test_session.exec(select(Like).where(Like.post_id == 1))
    post = result.first()
    assert post.post_id == 1  # type: ignore
    assert post.user_id == 1  # type: ignore


# 존재하지 않는 포스트에 좋아요 추가
@pytest.mark.asyncio
@pytest.mark.create
async def test_create_like_post_not_exists(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # given
    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )

    # when
    response = await test_client.post(
        url="/likes/",
        json={
            "post_id": 1,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "존재하지 않는 포스트입니다"


# 포스트에 좋아요 중복 추가
@pytest.mark.asyncio
@pytest.mark.create
async def test_create_like_duplicate(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # given
    user_result = await test_session.exec(
        select(User).where(User.nickname == "test_user")
    )
    user = user_result.first()
    user_id = user.id  # type: ignore
    test_post = Post(author_id=user_id, title="test_title_1", content="test_content_1")  # type: ignore
    test_session.add(test_post)
    await test_session.commit()
    await test_session.refresh(test_post)
    post_id = test_post.id  # type: ignore
    test_like = Like(user_id=user_id, post_id=post_id)  # type: ignore
    test_session.add(test_like)
    await test_session.commit()

    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )

    # when
    response = await test_client.post(
        "/likes/",
        json={
            "post_id": 1,
        },
    )

    # then
    assert response.status_code == 400
    assert response.json()["detail"] == "이미 좋아요 한 포스트입니다"


# 포스트에 좋아요 한 유저 조회
@pytest.mark.asyncio
@pytest.mark.get
async def test_get_like_users_ok(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # given
    user_result = await test_session.exec(
        select(User).where(User.nickname == "test_user")
    )
    user = user_result.first()
    user_id = user.id  # type: ignore
    test_post = Post(author_id=user_id, title="test_title_1", content="test_content_1")  # type: ignore
    test_session.add(test_post)
    await test_session.commit()
    await test_session.refresh(test_post)
    post_id = test_post.id  # type: ignore
    test_like = Like(user_id=user_id, post_id=post_id)  # type: ignore
    test_session.add(test_like)
    await test_session.commit()

    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )

    # when
    response = await test_client.get("/likes/?post_id=1")

    # then
    assert response.status_code == 200
    assert len(response.json()["users"]) == 1


# 포스트에 좋아요 하지 않은 상태에서 유저 조회
@pytest.mark.asyncio
@pytest.mark.get
async def test_get_like_users_empty_ok(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # given
    user_result = await test_session.exec(
        select(User).where(User.nickname == "test_user")
    )
    user = user_result.first()
    user_id = user.id  # type: ignore
    test_post = Post(author_id=user_id, title="test_title_1", content="test_content_1")  # type: ignore
    test_session.add(test_post)
    await test_session.commit()

    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )

    # when
    response = await test_client.get("/likes/?post_id=1")

    # then
    assert response.status_code == 200
    assert len(response.json()["users"]) == 0


# 존재하지 않는 포스트에 좋아요 유저 조회
@pytest.mark.asyncio
@pytest.mark.get
async def test_get_like_users_not_exists(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # given
    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )

    # when
    response = await test_client.get("/likes/?post_id=1")

    assert response.status_code == 400
    assert response.json()["detail"] == "존재하지 않는 포스트입니다"


# 포스트에 좋아요 삭제
@pytest.mark.asyncio
@pytest.mark.delete
async def test_delete_like_ok(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    None
