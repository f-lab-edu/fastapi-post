import hashlib
from abc import ABCMeta, abstractmethod
from datetime import datetime

from fastapi import Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from ulid import ULID

from src.database import get_session_factory
from src.domains.like import Like
from src.domains.user import User


class LikeServiceBase(metaclass=ABCMeta):
    @abstractmethod
    async def create_like(self, user_id: int, post_id: int) -> Like:
        pass

    @abstractmethod
    async def get_like_by_user_and_post(
        self, user_id: int, post_id: int
    ) -> Like | None:
        pass

    @abstractmethod
    async def get_like(self, like_id: int) -> Like | None:
        pass

    @abstractmethod
    async def get_liked_users(self, post_id: int | None = None) -> list[User]:
        pass

    @abstractmethod
    async def delete_like(self, like: Like) -> None:
        pass


class LikeService(LikeServiceBase):
    def __init__(
        self, session_factory: AsyncSession = Depends(get_session_factory)
    ) -> None:
        self.session_factory = session_factory

    async def create_like(self, user_id: int, post_id: int) -> Like:
        new_post_id = str(ULID.from_datetime(datetime.now()))
        sharding_key = int(hashlib.md5(new_post_id.encode()).hexdigest(), 16) % (2**30)
        async with self.session_factory(sharding_key) as session:  # type: ignore
            new_like = Like(id=sharding_key, user_id=user_id, post_id=post_id)
            session.add(new_like)
            await session.commit()
            await session.refresh(new_like)
            return new_like

    async def get_like_by_user_and_post(
        self, user_id: int, post_id: int
    ) -> Like | None:
        new_post_id = str(ULID.from_datetime(datetime.now()))
        sharding_key = int(hashlib.md5(new_post_id.encode()).hexdigest(), 16) % (2**30)
        async with self.session_factory(sharding_key) as session:  # type: ignore
            result = await session.exec(
                select(Like).where(Like.user_id == user_id, Like.post_id == post_id)
            )
            like = result.first()

            return like  # type: ignore

    async def get_like(self, like_id: int) -> Like | None:
        async with self.session_factory(like_id) as session:  # type: ignore

            orm_query = select(Like).where(Like.id == like_id)
            result = await session.exec(orm_query)
            like = result.first()

            return like  # type: ignore

    async def get_liked_users(self, post_id: int | None = None) -> list[User]:
        new_post_id = str(ULID.from_datetime(datetime.now()))
        sharding_key = int(hashlib.md5(new_post_id.encode()).hexdigest(), 16) % (2**30)
        async with self.session_factory(sharding_key) as session:  # type: ignore

            orm_query = select(User).join(Like)
            if post_id:
                orm_query = orm_query.where(Like.post_id == post_id)
            result = await session.exec(orm_query)
            like_users = result.all()

            return list(like_users)

    async def delete_like(self, like: Like) -> None:
        async with self.session_factory(like.id) as session:  # type: ignore

            await session.delete(like)
            await session.commit()
