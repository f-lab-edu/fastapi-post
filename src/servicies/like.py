from abc import ABCMeta, abstractmethod

from fastapi import Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_session
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
    def __init__(self, session: AsyncSession = Depends(get_session)) -> None:
        self.session = session

    async def create_like(self, user_id: int, post_id: int) -> Like:
        new_like = Like(user_id=user_id, post_id=post_id)
        self.session.add(new_like)
        await self.session.commit()
        await self.session.refresh(new_like)

        return new_like

    async def get_like_by_user_and_post(
        self, user_id: int, post_id: int
    ) -> Like | None:
        result = await self.session.exec(
            select(Like).where(Like.user_id == user_id, Like.post_id == post_id)
        )
        like = result.first()

        return like

    async def get_like(self, like_id: int) -> Like | None:
        orm_query = select(Like).where(Like.id == like_id)
        result = await self.session.exec(orm_query)
        like = result.first()

        return like

    async def get_liked_users(self, post_id: int | None = None) -> list[User]:
        orm_query = select(User).join(Like)
        if post_id:
            orm_query = orm_query.where(Like.post_id == post_id)
        result = await self.session.exec(orm_query)
        like_users = result.all()

        return list(like_users)

    async def delete_like(self, like: Like) -> None:
        await self.session.delete(like)
        await self.session.commit()
