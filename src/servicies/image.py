import os

from fastapi import Depends
from sqlalchemy import update
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import config
from src.database import get_session
from src.domains.user import User


class ImageService:
    def __init__(self, session: AsyncSession = Depends(get_session)) -> None:
        self.session = session

    async def save_profile_img(
        self, user_id: int, img_name: str, img_content: bytes
    ) -> str:
        # save DB
        result = await self.session.exec(select(User).where(User.id == user_id))
        user = result.first()
        prev_profile_img_url = user.profile_img_url  # type: ignore
        profile_image_url = os.path.join(config.UPLOAD_DIR, img_name)

        # save File
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
