from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from config import Config
from main import app
from src.auth import hash_password
from src.database import get_session
from src.domains.user import User


TEST_DATABASE_URL = Config().TEST_DATABASE_URL


@pytest_asyncio.fixture(scope="function")
async def test_db_init():
    test_engine = create_async_engine(url=TEST_DATABASE_URL, future=True)
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    yield test_engine

    await test_engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_db_init: AsyncEngine) -> AsyncSession:
    AsyncSessionLocal = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_init,
        class_=AsyncSession,
    )
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
def test_client(test_session: AsyncSession):
    async def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test/users")
    yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.create
async def test_signup_user_ok(test_client: AsyncClient, test_session: AsyncSession):
    # when
    response = await test_client.post(
        "/",
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
):
    # when
    response = await test_client.post(
        "/",
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
):
    # when
    response = await test_client.post(
        "/",
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
):
    # given
    hashed_password = hash_password(plain_password="Test_password")
    new_user = User(nickname="test_user", password=hashed_password)
    test_session.add(new_user)
    await test_session.commit()

    # when
    response = await test_client.post(
        "/",
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
async def test_login_ok(test_client: AsyncClient, test_session: AsyncSession):
    # given
    hashed_password = hash_password(plain_password="Test_password")
    new_user = User(nickname="test_user", password=hashed_password)
    test_session.add(new_user)
    await test_session.commit()

    # when
    response = await test_client.post(
        "/login",
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
):
    # given
    hashed_password = hash_password(plain_password="Test_password")
    new_user = User(nickname="test_user", password=hashed_password)
    test_session.add(new_user)
    await test_session.commit()

    # when
    response = await test_client.post(
        "/login",
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
):
    # given
    hashed_password = hash_password(plain_password="Test_password")
    new_user = User(nickname="test_user", password=hashed_password)
    test_session.add(new_user)
    await test_session.commit()

    # when
    response = await test_client.post(
        "/login",
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
async def test_logout_ok(test_client: AsyncClient, test_session: AsyncSession):
    # given
    hashed_password = hash_password(plain_password="Test_password")
    new_user = User(nickname="test_user", password=hashed_password)
    test_session.add(new_user)
    await test_session.commit()

    # when
    await test_client.post(
        "/login",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )
    response = await test_client.post("/logout")

    # then
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.logout
async def test_logout_invalid_session_id(
    test_client: AsyncClient, test_session: AsyncSession
):
    # given
    hashed_password = hash_password(plain_password="Test_password")
    new_user = User(nickname="test_user", password=hashed_password)
    test_session.add(new_user)
    await test_session.commit()

    # when
    response = await test_client.post(
        "/login",
        json={
            "nickname": "test_user",
            "password": "Test_password",
        },
    )
    test_client.cookies = {"session_id": "invalid_session_id"}
    response = await test_client.post("/logout")

    # then
    assert response.status_code == 400
    assert response.json()["detail"] == "존재하지 않는 세션입니다"
