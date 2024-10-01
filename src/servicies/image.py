import asyncio
import os

from fastapi import Depends, UploadFile
from google.cloud import storage
from sqlalchemy import update
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import config
from src.database import get_session
from src.domains.image import Image, SaveType, State, UseType


class ImageService:
    def __init__(self, session: AsyncSession = Depends(get_session)) -> None:
        self.session = session

    async def save_profile_img(
        self, user_id: int, img_name: str, img_content: UploadFile, save_type: SaveType
    ) -> str:
        prev_image_result = await self.session.exec(
            select(Image).where(Image.user_id == user_id, Image.state == State.ACTIVE)
        )
        prev_image = prev_image_result.first()

        file_contents = await img_content.read()

        new_image = Image(
            name=img_name,
            path=img_name,
            save_type=save_type,
            use_type=UseType.USER_PROFILE,
            state=State.ACTIVE,
            user_id=user_id,
        )
        self.session.add(new_image)
        await self.session.flush()

        if prev_image:
            try:
                await self.remove_previous_image(prev_image.id, prev_image.type)  # type: ignore
            except:
                pass

        if save_type == SaveType.GCP:
            await self.save_gcp(
                bucket_name="fastapi-post-storage",
                contents=file_contents,
                content_type=img_content.content_type,  # type: ignore
                destination_blob_name=img_name,
            )
        elif save_type == SaveType.LOCAL:
            await self.save_local(img_name, file_contents)

        await self.session.commit()

        return img_name

    async def remove_previous_image(self, prev_image_id: int, save_type: SaveType):
        result = await self.session.exec(select(Image).where(Image.id == prev_image_id))
        prev_image = result.first()

        if prev_image:
            if save_type == SaveType.LOCAL:
                file_path = os.path.join(config.LOCAL_UPLOAD_DIR, prev_image.name)
                if os.path.exists(file_path):
                    os.remove(file_path)
            elif save_type == SaveType.GCP:
                storage_client = storage.Client()
                bucket = storage_client.bucket("fastapi-post-storage")
                blob = bucket.blob(prev_image.name)
                await asyncio.get_event_loop().run_in_executor(None, blob.delete)

            await self.session.exec(  # type: ignore
                update(Image)
                .where(Image.id == prev_image_id)  # type: ignore
                .values(state=State.PENDING)
            )

    async def save_local(self, img_name: str, contents: bytes) -> None:
        profile_image_url = os.path.join(config.LOCAL_UPLOAD_DIR, img_name)
        with open(profile_image_url, "wb") as fp:
            fp.write(contents)

    async def save_gcp(
        self,
        bucket_name: str,
        contents: bytes,
        content_type: str,
        destination_blob_name: str,
    ) -> None:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        # 비동기 실행을 위해 run_in_executor 사용
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: blob.upload_from_string(contents, content_type=content_type)
        )
