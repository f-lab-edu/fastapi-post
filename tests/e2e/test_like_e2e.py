import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth import hash_password
from src.config import config
from src.domains.like import Like
from src.domains.post import Post
from src.domains.post_view import PostView
from src.domains.user import User
from src.main import app

DATABASE_URL = config.DATABASE_URL


@pytest_asyncio.fixture
async def test_client(test_session: AsyncSession) -> AsyncClient:
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    hashed_password = hash_password(plain_password="Test_password")
    new_user = User(nickname="test_user", password=hashed_password)
    test_session.add(new_user)
    await test_session.commit()

    yield client


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
        Post(
            id=1,
            author_id=user.id,  # type: ignore
            title="test_title_1",
            content="test_content_1",
        )
    )
    test_session.add(PostView(post_id=1))
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
    test_post = Post(
        id=1,
        author_id=user_id,
        title="test_title_1",
        content="test_content_1",
    )  # type: ignore
    test_session.add(test_post)
    test_session.add(PostView(post_id=1))
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
async def test_get_liked_users_ok(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # given
    user_result = await test_session.exec(
        select(User).where(User.nickname == "test_user")
    )
    user = user_result.first()
    user_id = user.id  # type: ignore
    test_post = Post(
        id=1,
        author_id=user_id,
        title="test_title_1",
        content="test_content_1",
    )  # type: ignore
    test_session.add(test_post)
    test_session.add(PostView(post_id=1))
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
async def test_get_liked_users_empty_ok(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # given
    user_result = await test_session.exec(
        select(User).where(User.nickname == "test_user")
    )
    user = user_result.first()
    user_id = user.id  # type: ignore
    test_post = Post(
        id=1,
        author_id=user_id,
        title="test_title_1",
        content="test_content_1",
    )  # type: ignore
    test_session.add(test_post)
    test_session.add(PostView(post_id=1))
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
async def test_get_liked_users_not_exists(
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

    # then
    assert response.status_code == 400
    assert response.json()["detail"] == "존재하지 않는 포스트입니다"


# 포스트에 좋아요 삭제
@pytest.mark.asyncio
@pytest.mark.delete
async def test_delete_like_ok(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # given
    user_result = await test_session.exec(
        select(User).where(User.nickname == "test_user")
    )
    user = user_result.first()
    user_id = user.id  # type: ignore
    test_post = Post(
        id=1,
        author_id=user_id,
        title="test_title_1",
        content="test_content_1",
    )  # type: ignore
    test_session.add(test_post)
    test_session.add(PostView(post_id=1))
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
    response = await test_client.delete("/likes/1")

    # then
    assert response.status_code == 204

    result = await test_session.exec(select(Like).where(Like.post_id == 1))
    post = result.first()
    assert post is None  # type: ignore


@pytest.mark.asyncio
@pytest.mark.delete
async def test_delete_like_post_not_like(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # given
    user_result = await test_session.exec(
        select(User).where(User.nickname == "test_user")
    )
    user = user_result.first()
    user_id = user.id  # type: ignore
    test_post = Post(
        id=1,
        author_id=user_id,
        title="test_title_1",
        content="test_content_1",
    )  # type: ignore
    test_session.add(test_post)
    test_session.add(PostView(post_id=1))
    await test_session.commit()
    await test_session.refresh(test_post)

    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )

    # when
    response = await test_client.delete("/likes/1")

    assert response.status_code == 400
    assert response.json()["detail"] == "좋아요 하지 않은 포스트입니다"
