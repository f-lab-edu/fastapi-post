import asyncio
import hashlib
import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, UploadFile
from google.cloud import storage
from sqlalchemy import update
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from ulid import ULID

from src.config import config
from src.database import DATABASE_URLS, get_session_factory
from src.domains.image import Image, SaveType, State, UseType
from src.gcp_client import gcp_client


class ImageService:
    def __init__(
        self, session_factory: AsyncSession = Depends(get_session_factory)
    ) -> None:
        session_factory = session_factory

    async def save_profile_img(
        self,
        img_name: str,
        img_content: UploadFile,
        save_type: SaveType,
        user_id: int | None = None,
    ) -> Image:
        new_id = str(ULID.from_datetime(datetime.now()))
        sharding_key = int(hashlib.md5(new_id.encode()).hexdigest(), 16) % (2**30)
        async with self.session_factory(sharding_key) as session:  # type: ignore
            prev_image_result = await session.exec(
                select(Image).where(
                    Image.user_id == user_id, Image.state == State.ACTIVE
                )
            )
            prev_image = prev_image_result.first()

            file_contents = await img_content.read()

            # 가입시 이미지 업로드 할 경우 user_id가 None. PENDING으로 회원가입 완료 대기.
            image_state = State.ACTIVE if user_id else State.PENDING
            new_image = Image(
                id=sharding_key,
                name=img_name,
                save_type=save_type,
                use_type=UseType.USER_PROFILE,
                state=image_state,
                user_id=user_id,
            )
            session.add(new_image)
            await session.flush()

            if prev_image:
                try:
                    await self.remove_previous_image(prev_image.id, prev_image.save_type)  # type: ignore
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

            await session.commit()
            await session.refresh(new_image)

            return new_image

    async def remove_previous_image(self, prev_image_id: int, save_type: SaveType):
        async with self.session_factory(prev_image_id) as session:  # type: ignore
            result = await session.exec(select(Image).where(Image.id == prev_image_id))
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

                await session.exec(  # type: ignore
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
        bucket = gcp_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        # 비동기 실행을 위해 run_in_executor 사용
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: blob.upload_from_string(contents, content_type=content_type)
        )

    async def remove_old_pending_images(self) -> None:
        one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
        for i in range(len(DATABASE_URLS)):
            async with self.session_factory(i) as session:  # type: ignore
                result = await session.exec(
                    select(Image).where(
                        Image.state == State.PENDING, Image.created_at < one_day_ago
                    )
                )
                old_pending_images = result.all()
                for image in old_pending_images:
                    await session.delete(image)
