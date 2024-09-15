from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth import hash_password
from src.config import config
from src.database import get_session
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
    None


# 포스트에 좋아요 삭제
@pytest.mark.asyncio
@pytest.mark.create
async def test_delete_like_ok(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    None


# 포스트에 좋아요 한 유저 조회
@pytest.mark.asyncio
@pytest.mark.create
async def test_get_like_by_post_id_ok(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    None
