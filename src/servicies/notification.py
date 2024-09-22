from abc import ABCMeta, abstractmethod

from fastapi import Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_session
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
    def __init__(self, session: AsyncSession = Depends(get_session)) -> None:
        self.session = session

    async def create_notification(
        self, user_id: int, actor_user_id: int, post_id: int
    ) -> Notification:
        new_notification = Notification(
            target_user_id=user_id, actor_user_id=actor_user_id, post_id=post_id
        )
        self.session.add(new_notification)
        await self.session.commit()
        await self.session.refresh(new_notification)

        return new_notification

    async def get_notifications_by_user_id(self, user_id: int) -> list[Notification]:
        result = await self.session.exec(
            select(Notification).where(Notification.target_user_id == user_id)
        )
        notifications = result.all()

        return list(notifications)
