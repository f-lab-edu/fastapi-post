import hashlib
from datetime import datetime

from fastapi import Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from ulid import ULID

from src.database import get_session_factory
from src.domains.comment import Comment


class CommentService:
    def __init__(
        self, session_factory: AsyncSession = Depends(get_session_factory)
    ) -> None:
        self.items_per_page = 20
        self.session_factory = session_factory

    async def create_comment(self, user_id: int, post_id: int, content: str) -> Comment:
        new_id = str(ULID.from_datetime(datetime.now()))
        sharding_key = int(hashlib.md5(new_id.encode()).hexdigest(), 16) % (2**30)
        new_comment = Comment(
            id=sharding_key, author_id=user_id, post_id=post_id, content=content
        )
        async with self.session_factory(sharding_key) as session:  # type: ignore
            session.add(new_comment)
            await session.commit()
            await session.refresh(new_comment)

            return new_comment

    async def get_comments(
        self, page: int, post_id: int | None = None, user_id: int | None = None
    ) -> list[Comment]:
        offset = (page - 1) * self.items_per_page
        results: list[Comment] = []
        orm_query = select(Comment)
        # TODO 이거 문제. 여러개 걸침.
        if post_id:
            orm_query = orm_query.where(Comment.post_id == post_id)
        if user_id:
            orm_query = orm_query.where(Comment.author_id == user_id)
        orm_query = orm_query.offset(offset).limit(self.items_per_page)
        async with self.session_factory(post_id) as session:  # type: ignore
            result = await session.exec(orm_query)
            comments = result.all()

            return list(comments)

    async def get_comment(self, comment_id: int) -> Comment | None:
        async with self.session_factory(comment_id) as session:  # type: ignore
            result = await session.exec(select(Comment).where(Comment.id == comment_id))
            comment: Comment | None = result.first()

            return comment

    async def edit_comment(self, comment: Comment, content: str | None = None) -> None:
        if content:
            comment.content = content
        async with self.session_factory(comment.id) as session:  # type: ignore
            session.add(comment)
            await session.commit()

    async def delete_comment(self, comment: Comment) -> None:
        async with self.session_factory(comment.id) as session:  # type: ignore
            await session.delete(comment)
            await session.commit()
