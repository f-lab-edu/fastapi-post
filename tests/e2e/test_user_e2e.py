# type: ignore

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth import hash_password
from src.config import config
from src.database import get_session
from src.domains.user import User
from src.main import app

DATABASE_URL = config.DATABASE_URL


@pytest.fixture
def test_client(test_session: AsyncSession) -> AsyncClient:
    async def override_get_session() -> AsyncSession:
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    yield client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.create
async def test_signup_user_ok(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # when
    response = await test_client.post(
        "/users/",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )

    # then
    assert response.status_code == 201
    assert response.json() == {"id": 1, "nickname": "test_user"}

    result = await test_session.exec(select(User).where(User.nickname == "test_user"))
    user = result.first()
    assert user.nickname == "test_user"


@pytest.mark.asyncio
@pytest.mark.create
async def test_signup_user_not_upper(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # when
    response = await test_client.post(
        "/users/",
        json={
            "nickname": "test_user",
            "password": "test_password",
        },
    )

    # then
    assert response.status_code == 400
    assert response.json()["detail"] == "문자열에 대문자가 하나 이상 포함되어야 합니다"

    result = await test_session.exec(select(User).where(User.nickname == "test_user"))
    user = result.first()
    assert user == None


@pytest.mark.asyncio
@pytest.mark.create
async def test_signup_user_invalid_params(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # when
    response = await test_client.post(
        "/users/",
        json={
            "nickname": "",
            "password": "",
        },
    )

    # then
    assert response.status_code == 422

    result = await test_session.exec(select(User).where(User.nickname == "test_user"))
    user = result.first()
    assert user == None


@pytest.mark.asyncio
@pytest.mark.create
async def test_signup_user_duplicate(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # given
    hashed_password = hash_password(plain_password="Test_password")
    new_user = User(nickname="test_user", password=hashed_password)
    test_session.add(new_user)
    await test_session.commit()

    # when
    response = await test_client.post(
        "/users/",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )

    # then
    assert response.status_code == 409
    assert response.json()["detail"] == "이미 가입한 유저입니다"

    result = await test_session.exec(select(User).where(User.nickname == "test_user"))
    user = result.first()
    assert user.nickname == "test_user"


@pytest.mark.asyncio
@pytest.mark.login
async def test_login_ok(test_client: AsyncClient, test_session: AsyncSession) -> None:
    # given
    hashed_password = hash_password(plain_password="Test_password")
    new_user = User(nickname="test_user", password=hashed_password)
    test_session.add(new_user)
    await test_session.commit()

    # when
    response = await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )

    # then
    assert response.status_code == 200
    assert response.json()["session_id"]


@pytest.mark.asyncio
@pytest.mark.login
async def test_login_invalid_nikcname(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # given
    hashed_password = hash_password(plain_password="Test_password")
    new_user = User(nickname="test_user", password=hashed_password)
    test_session.add(new_user)
    await test_session.commit()

    # when
    response = await test_client.post(
        "/users/login",
        json={
            "nickname": "invalid_user",
            "password": "Test_password",
        },
    )

    # then
    assert response.status_code == 401
    assert response.json()["detail"] == "존재하지 않는 유저입니다"


@pytest.mark.asyncio
@pytest.mark.login
async def test_login_invalid_password(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # given
    hashed_password = hash_password(plain_password="Test_password")
    new_user = User(nickname="test_user", password=hashed_password)
    test_session.add(new_user)
    await test_session.commit()

    # when
    response = await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user",
            "password": "invalid_password",
        },
    )

    # then
    assert response.status_code == 401
    assert response.json()["detail"] == "잘못된 비밀번호입니다"


@pytest.mark.asyncio
@pytest.mark.logout
async def test_logout_ok(test_client: AsyncClient, test_session: AsyncSession) -> None:
    # given
    hashed_password = hash_password(plain_password="Test_password")
    new_user = User(nickname="test_user", password=hashed_password)
    test_session.add(new_user)
    await test_session.commit()

    # when
    await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )
    response = await test_client.post("/users/logout")

    # then
    assert response.status_code == 204


@pytest.mark.asyncio
@pytest.mark.logout
async def test_logout_invalid_session_id(
    test_client: AsyncClient, test_session: AsyncSession
) -> None:
    # given
    hashed_password = hash_password(plain_password="Test_password")
    new_user = User(nickname="test_user", password=hashed_password)
    test_session.add(new_user)
    await test_session.commit()

    # when
    response = await test_client.post(
        "/users/login",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )
    test_client.cookies = {"session_id": "invalid_session_id"}
    response = await test_client.post("/users/logout")

    # then
    assert response.status_code == 400
    assert response.json()["detail"] == "존재하지 않는 세션입니다"
