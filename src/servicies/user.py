import os
from typing import List

from fastapi import Depends
from sqlalchemy import update
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth import hash_password
from src.config import config
from src.database import get_session
from src.domains.notification import Notification
from src.domains.user import User


class UserService:
    def __init__(self, session: AsyncSession = Depends(get_session)) -> None:
        self.session = session

    async def signup_account(self, nickname: str, password: str) -> User:
        hashed_password = hash_password(plain_password=password)
        new_user = User(nickname=nickname, password=hashed_password)

        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)

        return new_user

    async def get_user_by_nickname(self, nickname: str) -> User | None:
        result = await self.session.exec(select(User).where(User.nickname == nickname))
        user = result.first()

        return user

    async def get_user(self, user_id: int) -> User | None:
        result = await self.session.exec(select(User).where(User.id == user_id))
        user = result.first()

        return user

    async def get_user_notification(self, user_id: int) -> List[Notification]:
        result = await self.session.exec(select(Notification).where(User.id == user_id))
        notifications = result.all()

        return list(notifications)

    async def save_profile_img(
        self, user_id: int, img_name: str, img_content: bytes
    ) -> str:
        result = await self.session.exec(select(User).where(User.id == user_id))
        user = result.first()
        prev_profile_img_url = user.profile_img_url  # type: ignore
        profile_image_url = os.path.join(config.UPLOAD_DIR, img_name)

        with open(profile_image_url, "wb") as fp:
            fp.write(img_content)
            await self.session.exec(  # type: ignore
                update(User)
                .where(User.id == user_id)  # type: ignore
                .values(profile_img_url=profile_image_url)
            )
        if prev_profile_img_url:
            if os.path.exists(prev_profile_img_url):
                os.remove(prev_profile_img_url)

        await self.session.commit()

        return profile_image_url
