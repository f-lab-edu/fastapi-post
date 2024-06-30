from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlmodel import create_engine, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession


DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = AsyncEngine(create_engine(DATABASE_URL, echo=True, future=True))


async def db_init(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    yield


async def get_session() -> AsyncSession:
    AsyncSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        class_=AsyncSession,
    )
    async with AsyncSessionLocal() as session:
        yield session
