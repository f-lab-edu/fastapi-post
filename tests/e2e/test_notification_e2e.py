import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth import hash_password
from src.config import config
from src.domains.notification import Notification
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
async def test_get_notifications_ok(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # given
    user_result = await test_session.exec(
        select(User).where(User.nickname == "test_user")
    )
    user = user_result.first()
    hashed_password = hash_password(plain_password="Test_password")
    new_user = User(id=2, nickname="test_user_2", password=hashed_password)
    test_session.add(new_user)
    test_session.add(
        Post(
            id=1,
            author_id=user.id,  # type: ignore
            title="test_title_1",
            content="test_content_1",
        )
    )
    test_session.add(PostView(post_id=1))
    test_session.add(Notification(actor_user_id=1, target_user_id=1, post_id=1))
    await test_session.commit()
    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )

    # when
    response = await test_client.get("/notifications/")

    # then
    assert response.status_code == 200
    assert len(response.json()) == 1
