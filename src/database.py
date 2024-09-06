from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import config

DATABASE_URL = config.DATABASE_URL
REDIS_URL = config.REDIS_URL
engine = AsyncEngine(create_engine(url=DATABASE_URL, pool_size=20, max_overflow=0))
redis = aioredis.from_url(url=REDIS_URL, encoding="utf-8", decode_responses=True)


@asynccontextmanager
async def db_init(app: FastAPI):
    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    yield


async def get_session() -> AsyncSession:  # type: ignore
    AsyncSessionLocal = sessionmaker(  # type: ignore
        autocommit=False,
        autoflush=False,
        bind=engine,
        class_=AsyncSession,
    )
    async with AsyncSessionLocal() as session:
        yield session


async def get_redis():
    if redis.connection:
        return redis
    else:
        return None
