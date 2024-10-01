import os

from fastapi import Depends
from sqlalchemy import update
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth import hash_password
from src.config import config
from src.database import get_session
from src.domains.image import Image, State, UseType
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
        result = await self.session.exec(
            select(User)
            .options(
                selectinload(
                    User.images.and_(  # type: ignore
                        Image.state == State.ACTIVE,
                        Image.use_type == UseType.USER_PROFILE,
                    )
                )
            )
            .where(User.id == user_id)
        )
        user = result.first()
        return user

    async def save_profile_img(
        self, user_id: int, img_name: str, img_content: bytes
    ) -> str:
        result = await self.session.exec(
            select(User)
            .options(
                selectinload(User.images.and_(Image.state == State.ACTIVE, Image.use_type == UseType.USER_PROFILE))  # type: ignore
            )
            .where(User.id == user_id)
        )
        user = result.first()
        prev_profile_img_url = user.images[0].name if user.images else ""  # type: ignore
        profile_image_url = os.path.join(config.LOCAL_UPLOAD_DIR, img_name)

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
