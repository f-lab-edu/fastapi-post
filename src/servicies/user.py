import hashlib
from datetime import datetime

from fastapi import Depends
from sqlalchemy import update
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from ulid import ULID

from src.auth import hash_password
from src.database import DATABASE_URLS, get_session_factory
from src.domains.image import Image, State, UseType
from src.domains.user import User


class UserService:
    def __init__(
        self, session_factory: AsyncSession = Depends(get_session_factory)
    ) -> None:
        self.session_factory = session_factory

    async def signup_account(
        self, nickname: str, password: str, img_id: int | None = None
    ) -> User:
        hashed_password = hash_password(plain_password=password)
        new_id = str(ULID.from_datetime(datetime.now()))
        sharding_key = int(hashlib.md5(new_id.encode()).hexdigest(), 16) % (2**30)
        new_user = User(id=sharding_key, nickname=nickname, password=hashed_password)
        async with self.session_factory(sharding_key) as session:  # type: ignore
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            # image ACTIVE 처리
            if img_id:
                await session.exec(  # type: ignore
                    update(Image)
                    .where(Image.id == img_id)  # type: ignore
                    .values(state=State.ACTIVE, user_id=new_user.id)
                )
                await session.commit()

            return new_user

    async def get_user_by_nickname(self, nickname: str) -> User | None:
        for i in range(len(DATABASE_URLS)):
            async with self.session_factory(i) as session:  # type: ignore
                result = await session.exec(
                    select(User).where(User.nickname == nickname)
                )
                user = result.first()
                if user:
                    return user  # type: ignore

        return None

    async def get_user(self, user_id: int) -> User | None:
        async with self.session_factory(user_id) as session:  # type: ignore
            result = await session.exec(
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
            return user  # type: ignore
