import hashlib
from datetime import datetime

from fastapi import Depends
from sqlalchemy import update
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from ulid import ULID

from src.database import DATABASE_URLS, get_session_factory
from src.domains.post import Post
from src.domains.post_view import PostView


class PostService:
    def __init__(
        self, session_factory: AsyncSession = Depends(get_session_factory)
    ) -> None:
        self.items_per_page = 20
        self.session_factory = session_factory

    async def create_post(self, user_id: int, title: str, content: str) -> Post:
        # TODO 안맞음. str인데 포스트 아이디. 통일?
        new_post_id = str(ULID.from_datetime(datetime.now()))
        sharding_key = int(hashlib.md5(new_post_id.encode()).hexdigest(), 16) % (2**30)
        new_post = Post(
            id=sharding_key,
            author_id=user_id,
            title=title,
            content=content,
        )
        async with self.session_factory(sharding_key) as session:  # type: ignore
            session.add(new_post)
            await session.commit()
            await session.refresh(new_post)
            new_post_view = PostView(post_id=new_post.id)
            session.add(new_post_view)
            await session.commit()
            await session.refresh(new_post_view)
            await session.refresh(new_post)

            return new_post

    async def get_posts(self, page: int) -> list[Post]:
        offset = (page - 1) * self.items_per_page
        results: list[Post] = []
        for i in range(len(DATABASE_URLS)):
            async with self.session_factory(i) as session:  # type: ignore
                result = await session.exec(
                    select(Post)
                    .options(
                        selectinload(Post.comments),  # type: ignore
                        selectinload(Post.user),  # type: ignore
                        selectinload(Post.likes),  # type: ignore
                        selectinload(Post.post_view),  # type: ignore
                    )
                    .offset(offset)
                    .limit(self.items_per_page)
                )
                posts = result.all()
                results.extend(posts)

        return results

    async def increase_post_view(self, post_id: int) -> None:
        async with self.session_factory(post_id) as session:  # type: ignore
            result = await session.exec(
                select(PostView).where(PostView.post_id == post_id)
            )
            post_view = result.first()
            if post_view:
                await session.exec(  # type: ignore
                    update(PostView)
                    .where(PostView.post_id == post_id)  # type: ignore
                    .values(count=PostView.count + 1)
                )
            await session.commit()

    async def get_post(self, post_id: int) -> Post | None:
        async with self.session_factory(post_id) as session:  # type: ignore
            result = await session.exec(
                select(Post)
                .options(  # type: ignore
                    selectinload(Post.user),  # type: ignore
                )
                .where(Post.id == post_id)
            )
            post = result.first()
            if not post:
                return None

            return post  # type: ignore

    async def edit_post(
        self, post: Post, title: str | None = None, content: str | None = None
    ) -> None:
        if title:
            post.title = title
        if content:
            post.content = content
        async with self.session_factory(post.id) as session:  # type: ignore
            session.add(post)
            await session.commit()

    async def delete_post(self, post: Post) -> None:
        async with self.session_factory(post.id) as session:  # type: ignore
            post_view_result = await session.exec(
                select(PostView).where(PostView.post_id == post.id)
            )
            post_view = post_view_result.first()
            if post_view:
                await session.delete(post_view)
            await session.delete(post)
            await session.commit()
