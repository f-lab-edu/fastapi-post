from abc import *
from typing import List

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
    async def get_like_users(self, post_id: int | None = None) -> List[User]:
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

    async def get_like_users(self, post_id: int | None = None) -> List[User]:
        orm_query = select(User).join(Like)
        if post_id:
            orm_query = orm_query.where(Like.post_id == post_id)
        result = await self.session.exec(orm_query)
        like_users = result.all()

        return list(like_users)
