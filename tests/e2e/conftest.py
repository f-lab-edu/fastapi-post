# type: ignore

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from testcontainers.mysql import MySqlContainer


@pytest_asyncio.fixture(scope="session")
async def test_db_container() -> MySqlContainer:
    mysql_container = MySqlContainer("mysql:lts")
    with mysql_container as container:
        yield container


@pytest_asyncio.fixture(scope="function")
async def test_engine(test_db_container: MySqlContainer) -> AsyncEngine:
    db_url = test_db_container.get_connection_url().replace("pymysql", "aiomysql")
    engine = create_async_engine(url=db_url)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine: AsyncEngine) -> AsyncSession:
    AsyncSessionLocal = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        bind=test_engine,
        class_=AsyncSession,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSessionLocal() as session:
        yield session
