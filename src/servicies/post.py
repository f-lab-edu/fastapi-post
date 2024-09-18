from typing import List

from fastapi import Depends
from sqlalchemy import update
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_session
from src.domains.post import Post
from src.domains.post_view import PostView


class PostService:
    def __init__(self, session: AsyncSession = Depends(get_session)) -> None:
        self.session = session
        self.items_per_page = 20

    async def create_post(self, user_id: int, title: str, content: str) -> Post:
        new_post_view = PostView()
        self.session.add(new_post_view)
        await self.session.commit()
        await self.session.refresh(new_post_view)
        new_post = Post(
            author_id=user_id,
            title=title,
            content=content,
            post_view_id=new_post_view.id,
        )

        self.session.add(new_post)
        await self.session.commit()
        await self.session.refresh(new_post)

        return new_post

    async def get_posts(self, page: int) -> List[Post]:
        offset = (page - 1) * self.items_per_page
        result = await self.session.exec(
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

        return list(posts)

    async def increase_post_view(self, post_view_id: int) -> None:
        result = await self.session.exec(
            select(PostView).where(PostView.id == post_view_id)
        )
        post_view = result.first()
        if post_view:
            await self.session.exec(  # type: ignore
                update(PostView)
                .where(PostView.id == post_view_id)  # type: ignore
                .values(count=PostView.count + 1)
            )
        await self.session.commit()

    async def get_post(self, post_id: int) -> Post | None:
        result = await self.session.exec(
            select(Post)
            .options(  # type: ignore
                selectinload(Post.user),  # type: ignore
            )
            .where(Post.id == post_id)
        )
        post = result.first()
        if not post:
            return None

        return post

    async def edit_post(
        self, post: Post, title: str | None = None, content: str | None = None
    ) -> None:
        if title:
            post.title = title
        if content:
            post.content = content

        self.session.add(post)
        await self.session.commit()

    async def delete_post(self, post: Post) -> None:
        await self.session.delete(post)
        await self.session.commit()
