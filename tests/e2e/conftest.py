# type: ignore

from contextlib import asynccontextmanager

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from testcontainers.mysql import MySqlContainer

from src.database import get_session_factory
from src.main import app


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

        async def test_get_session_factory():
            @asynccontextmanager
            async def _test_get_session(key=None):
                print("1->", id(session))
                yield session

            return _test_get_session

        app.dependency_overrides[get_session_factory] = test_get_session_factory
        print("2->", id(session))
        yield session

    app.dependency_overrides.clear()
