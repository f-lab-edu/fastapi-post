from abc import ABCMeta, abstractmethod

from fastapi import Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_session_factory
from src.domains.notification import Notification


class NotificationServiceBase(metaclass=ABCMeta):
    @abstractmethod
    async def create_notification(
        self, user_id: int, actor_user_id: int, post_id: int
    ) -> Notification:
        pass

    @abstractmethod
    async def get_notifications_by_user_id(self, user_id: int) -> list[Notification]:
        pass


class NotificationService(NotificationServiceBase):
    def __init__(
        self, session_factory: AsyncSession = Depends(get_session_factory)
    ) -> None:
        self.session_factory = session_factory

    async def create_notification(
        self, user_id: int, actor_user_id: int, post_id: int
    ) -> Notification:
        new_notification = Notification(
            target_user_id=user_id, actor_user_id=actor_user_id, post_id=post_id
        )
        async with self.session_factory(user_id) as session:  # type: ignore
            session.add(new_notification)
            await session.commit()
            await session.refresh(new_notification)

            return new_notification

    async def get_notifications_by_user_id(self, user_id: int) -> list[Notification]:
        async with self.session_factory(user_id) as session:  # type: ignore
            result = await session.exec(
                select(Notification).where(Notification.target_user_id == user_id)
            )
            notifications = result.all()

            return list(notifications)
