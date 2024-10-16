# type: ignore

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth import hash_password
from src.config import config
from src.domains.comment import Comment
from src.domains.post import Post
from src.domains.post_view import PostView
from src.domains.user import Role, User
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
async def test_create_comment_ok(
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
    response = await test_client.post(
        "/comments/",
        json={
            "post_id": 1,
            "content": "test_comment",
        },
    )

    # then
    assert response.status_code == 201
    assert response.json()["content"] == "test_comment"

    result = await test_session.exec(
        select(Comment).where(Comment.content == "test_comment")
    )
    post = result.first()
    assert post.content == "test_comment"


@pytest.mark.asyncio
@pytest.mark.create
async def test_create_comment_invalid_params(
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
    response = await test_client.post(
        url="/comments/",
        json={
            "post_id": 1,
            "content": None,
        },
    )

    # when
    assert response.status_code == 422

    result = await test_session.exec(
        select(Comment).where(Comment.content == "test_comment")
    )
    post = result.first()
    assert post == None


@pytest.mark.asyncio
@pytest.mark.create
async def test_create_comment_post_missing_field(
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
    response = await test_client.post(
        url="/comments/",
        json={"post_id": 1},
    )

    # then
    assert response.status_code == 422

    result = await test_session.exec(
        select(Comment).where(Comment.content == "test_comment")
    )
    post = result.first()
    assert post == None


@pytest.mark.asyncio
@pytest.mark.create
async def test_create_comment_post_not_exists(test_client: AsyncClient) -> None:
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
        url="/comments/",
        json={
            "post_id": 1,
            "content": "test_comment",
        },
    )

    # then
    assert response.status_code == 400
    assert response.json()["detail"] == "존재하지 않는 포스트입니다"


@pytest.mark.asyncio
@pytest.mark.comments
async def test_get_comments_by_post_ok(
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
    test_session.add(Comment(author_id=user.id, post_id=1, content="test_comment_1"))
    test_session.add(Comment(author_id=user.id, post_id=1, content="test_comment_2"))
    await test_session.commit()
    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )

    # when
    response = await test_client.get("/comments/?post_id=1")

    # then
    assert response.status_code == 200
    assert len(response.json()["comments"]) == 2


@pytest.mark.asyncio
@pytest.mark.comments
async def test_get_comments_by_post_empty_ok(
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
    response = await test_client.get("/comments/?post_id=1")

    # then
    assert response.status_code == 200
    assert len(response.json()["comments"]) == 0


@pytest.mark.asyncio
@pytest.mark.comments
async def test_get_comments_by_user_ok(
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
    test_session.add(Comment(author_id=user.id, post_id=1, content="test_comment_1"))
    test_session.add(Comment(author_id=user.id, post_id=1, content="test_comment_2"))
    await test_session.commit()
    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )

    # when
    response = await test_client.get("/comments/?user_id=1")

    # then
    assert response.status_code == 200
    assert len(response.json()["comments"]) == 2


@pytest.mark.asyncio
@pytest.mark.comments
async def test_get_comments_by_user_empty_ok(
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
    response = await test_client.get("/comments/?user_id=1")

    # then
    assert response.status_code == 200
    assert len(response.json()["comments"]) == 0


@pytest.mark.asyncio
@pytest.mark.comments
async def test_get_comments_by_post_and_user_ok(
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
    test_session.add(Comment(author_id=user.id, post_id=1, content="test_comment_1"))
    test_session.add(Comment(author_id=user.id, post_id=1, content="test_comment_2"))
    await test_session.commit()

    # when
    response = await test_client.get("/comments/?post_id=1&user_id=1")

    # then
    assert response.status_code == 200
    assert len(response.json()["comments"]) == 2


@pytest.mark.asyncio
@pytest.mark.comments
async def test_get_comments_by_post_and_user_empty_ok(
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
    response = await test_client.get("/comments/?post_id=1&user_id=1")

    # then
    assert response.status_code == 200
    assert len(response.json()["comments"]) == 0


@pytest.mark.asyncio
@pytest.mark.comments
async def test_get_comments_ok(
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
    test_session.add(Comment(author_id=user.id, post_id=1, content="test_comment_1"))
    test_session.add(Comment(author_id=user.id, post_id=1, content="test_comment_2"))
    await test_session.commit()

    # when
    response = await test_client.get("/comments/")

    # then
    assert response.status_code == 200
    assert len(response.json()["comments"]) == 2


@pytest.mark.asyncio
@pytest.mark.patch
async def test_comment_patch_ok(
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
    test_session.add(Comment(author_id=user.id, post_id=1, content="test_comment_1"))
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
        url="/comments/1", json={"content": "test_comment_1_edit"}
    )

    # then
    assert response.status_code == 204

    result = await test_session.exec(
        select(Comment).where(Comment.content == "test_comment_1_edit")
    )
    post = result.first()
    assert post.content == "test_comment_1_edit"


@pytest.mark.asyncio
@pytest.mark.patch
async def test_comment_patch_not_exists(
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
        url="/comments/1", json={"content": "test_comment_1_edit"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "존재하지 않는 코멘트입니다"


@pytest.mark.asyncio
@pytest.mark.patch
async def test_comment_patch_invalid_author(
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
    test_session.add(Comment(author_id=user.id, post_id=1, content="test_comment_1"))

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
        url="/comments/1", json={"content": "test_comment_1_edit"}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "작성자 또는 관리자만 수정할 수 있습니다"


@pytest.mark.asyncio
@pytest.mark.patch
async def test_comment_patch_admin_role(
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
    test_session.add(Comment(author_id=user.id, post_id=1, content="test_comment_1"))

    hashed_password = hash_password(plain_password="Test_password")
    new_user = User(nickname="test_user_2", password=hashed_password, role=Role.admin)
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
    # admin role로 수정 시도. 세션아이디 변경 됨
    test_client.cookies.delete("session_id")
    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user_2",
            "password": "Test_password",
        },
    )

    response = await test_client.patch(
        url="/comments/1", json={"content": "test_comment_1_edit"}
    )

    # then
    assert response.status_code == 204

    result = await test_session.exec(
        select(Comment).where(Comment.content == "test_comment_1_edit")
    )
    post = result.first()
    assert post.content == "test_comment_1_edit"


@pytest.mark.asyncio
@pytest.mark.delete
async def test_comment_delete_ok(
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
    test_session.add(Comment(author_id=user.id, post_id=1, content="test_comment_1"))
    await test_session.commit()
    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )

    # when
    delete_response = await test_client.delete(url="/comments/1")

    # then
    assert delete_response.status_code == 204

    result = await test_session.exec(
        select(Comment).where(Comment.content == "test_comment_1")
    )
    post = result.first()
    assert post == None


@pytest.mark.asyncio
@pytest.mark.delete
async def test_comment_delete_not_exists(
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
    response = await test_client.delete(url="/comments/1")

    assert response.status_code == 400
    assert response.json()["detail"] == "존재하지 않는 코멘트입니다"


@pytest.mark.asyncio
@pytest.mark.delete
async def test_comment_delete_invalid_author(
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
    test_session.add(Comment(author_id=user.id, post_id=1, content="test_comment_1"))
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

    response = await test_client.delete(url="/comments/1")

    assert response.status_code == 403
    assert response.json()["detail"] == "작성자 또는 관리자만 삭제할 수 있습니다"


@pytest.mark.asyncio
@pytest.mark.delete
async def test_comment_delete_admin_role(
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
    test_session.add(Comment(author_id=user.id, post_id=1, content="test_comment_1"))
    hashed_password = hash_password(plain_password="Test_password")
    new_user = User(nickname="test_user_2", password=hashed_password, role=Role.admin)
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
    # admin role로 수정 시도. 세션아이디 변경 됨
    test_client.cookies.delete("session_id")
    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user_2",
            "password": "Test_password",
        },
    )

    response = await test_client.delete(url="/comments/1")

    # then
    assert response.status_code == 204

    result = await test_session.exec(
        select(Comment).where(Comment.content == "test_comment_1")
    )
    post = result.first()
    assert post == None
