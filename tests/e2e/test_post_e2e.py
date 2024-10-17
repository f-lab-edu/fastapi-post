# type: ignore

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth import hash_password
from src.config import config
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


@pytest.mark.asyncio
@pytest.mark.create
async def test_create_post_ok(
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
        "/posts/",
        json={
            "title": "test_title",
            "content": "test_content",
        },
    )
    # then
    assert response.status_code == 201
    assert response.json()["id"]
    result = await test_session.exec(select(Post).where(Post.title == "test_title"))
    post = result.first()
    assert post.title == "test_title"


@pytest.mark.asyncio
@pytest.mark.create
async def test_create_post_invalid_params(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # when
    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )
    response = await test_client.post(
        "/posts/",
        json={
            "title": None,
            "content": None,
        },
    )

    # then
    assert response.status_code == 422

    result = await test_session.exec(select(Post))
    posts = result.all()
    assert len(posts) == 0


@pytest.mark.asyncio
@pytest.mark.posts
async def test_get_posts_ok(
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
            author_id=user.id,
            title="test_title_1",
            content="test_content_1",
        )
    )
    test_session.add(PostView(post_id=1))
    test_session.add(
        Post(
            id=2,
            author_id=user.id,
            title="test_title_1",
            content="test_content_1",
        )
    )
    test_session.add(PostView(post_id=2))
    await test_session.commit()

    # when
    response = await test_client.get("/posts/")

    # then
    assert response.status_code == 200
    assert len(response.json()["posts"]) == 2


@pytest.mark.asyncio
@pytest.mark.posts
async def test_get_posts_empty_ok(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # when
    response = await test_client.get("/posts/")

    # then
    assert response.status_code == 200
    assert len(response.json()["posts"]) == 0

    result = await test_session.exec(select(Post))
    posts = result.all()
    assert len(posts) == 0


@pytest.mark.asyncio
@pytest.mark.post
async def test_get_post_ok(
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
            author_id=user.id,
            title="test_title_1",
            content="test_content_1",
        )
    )
    test_session.add(PostView(post_id=1))
    await test_session.commit()

    # when
    response = await test_client.get("/posts/1")

    # then
    assert response.status_code == 200
    assert response.json()["title"] == "test_title_1"
    assert response.json()["content"] == "test_content_1"


# 여기부터
@pytest.mark.asyncio
@pytest.mark.post
async def test_get_post_not_exists(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # when
    response = await test_client.get("/posts/1")

    # then
    assert response.status_code == 400
    assert response.json()["detail"] == "존재하지 않는 포스트입니다"


@pytest.mark.asyncio
@pytest.mark.patch
async def test_post_patch_ok(
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
            author_id=user.id,
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
    response = await test_client.patch(
        url="/posts/1", json={"content": "test_content_1_edit"}
    )

    # then
    assert response.status_code == 204

    result = await test_session.exec(select(Post).where(Post.id == 1))
    post = result.first()
    assert post.content == "test_content_1_edit"


@pytest.mark.asyncio
@pytest.mark.patch
async def test_post_patch_not_exists(
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
    response = await test_client.patch(
        url="/posts/1", json={"content": "test_content_1_edit"}
    )

    # then
    assert response.status_code == 400
    assert response.json()["detail"] == "존재하지 않는 포스트입니다"


@pytest.mark.asyncio
@pytest.mark.patch
async def test_post_patch_invalid_author(
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
            author_id=user.id,
            title="test_title_1",
            content="test_content_1",
        )
    )
    test_session.add(PostView(post_id=1))
    hashed_password = hash_password(plain_password="Test_password")
    new_user = User(nickname="test_user_2", password=hashed_password)
    test_session.add(new_user)
    await test_session.commit()
    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )

    # when
    # 다른 아이디로 수정 시도. 세션아이디 변경 됨
    test_client.cookies.delete("session_id")
    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user_2",
            "password": "Test_password",
        },
    )

    response = await test_client.patch(
        url="/posts/1", json={"content": "test_content_1_edit"}
    )

    # then
    assert response.status_code == 403
    assert response.json()["detail"] == "작성자 또는 관리자만 수정할 수 있습니다"


@pytest.mark.asyncio
@pytest.mark.put
async def test_post_put_ok(
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
            author_id=user.id,
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
    response = await test_client.put(
        url="/posts/1",
        json={"title": "test_title_1_edit", "content": "test_content_1_edit"},
    )

    # then
    assert response.status_code == 204

    result = await test_session.exec(select(Post).where(Post.id == 1))
    post = result.first()
    assert post.title == "test_title_1_edit"
    assert post.content == "test_content_1_edit"


@pytest.mark.asyncio
@pytest.mark.put
async def test_post_put_not_exists(
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
    response = await test_client.put(
        url="/posts/1",
        json={"title": "test_title_1_edit", "content": "test_content_1_edit"},
    )

    # then
    assert response.status_code == 400
    assert response.json()["detail"] == "존재하지 않는 포스트입니다"


@pytest.mark.asyncio
@pytest.mark.put
async def test_post_put_invalid_author(
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
            author_id=user.id,
            title="test_title_1",
            content="test_content_1",
        )
    )
    test_session.add(PostView(post_id=1))
    hashed_password = hash_password(plain_password="Test_password")
    new_user = User(nickname="test_user_2", password=hashed_password)
    test_session.add(new_user)
    await test_session.commit()
    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )

    # when
    # 다른 아이디로 수정 시도. 세션아이디 변경 됨
    test_client.cookies.delete("session_id")
    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user_2",
            "password": "Test_password",
        },
    )

    response = await test_client.put(
        url="/posts/1",
        json={"title": "test_title_1_edit", "content": "test_content_1_edit"},
    )

    # then
    assert response.status_code == 403
    assert response.json()["detail"] == "작성자 또는 관리자만 수정할 수 있습니다"


@pytest.mark.asyncio
@pytest.mark.put
async def test_post_put_missing_field(
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
            author_id=user.id,
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
    response = await test_client.put(
        url=f"/posts/1", json={"content": "test_content_1_edit"}
    )

    # then
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.delete
async def test_post_delete_ok(
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
            author_id=user.id,
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
    delete_response = await test_client.delete(url="/posts/1")
    assert delete_response.status_code == 204

    # then
    result = await test_session.exec(select(Post).where(Post.id == 1))
    post = result.first()
    assert post == None


@pytest.mark.asyncio
@pytest.mark.delete
async def test_post_delete_invalid_author(
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
            author_id=user.id,
            title="test_title_1",
            content="test_content_1",
        )
    )
    test_session.add(PostView(post_id=1))

    hashed_password = hash_password(plain_password="Test_password")
    new_user = User(nickname="test_user_2", password=hashed_password)
    test_session.add(new_user)
    await test_session.commit()
    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )

    # 다른 아이디로 수정 시도. 세션아이디 변경 됨
    test_client.cookies.delete("session_id")
    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user_2",
            "password": "Test_password",
        },
    )

    response = await test_client.delete(url="/posts/1")

    assert response.status_code == 403
    assert response.json()["detail"] == "작성자 또는 관리자만 삭제할 수 있습니다"
