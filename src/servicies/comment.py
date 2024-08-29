from typing import List

from fastapi import Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_session
from src.domains.comment import Comment


class CommentService:
    def __init__(self, session: AsyncSession = Depends(get_session)) -> None:
        self.session = session
        self.items_per_page = 20

    async def create_comment(self, user_id: int, post_id: int, content: str) -> Comment:
        new_comment = Comment(author_id=user_id, post_id=post_id, content=content)

        self.session.add(new_comment)
        await self.session.commit()
        await self.session.refresh(new_comment)

        return new_comment

    async def get_comments(
        self, page: int, post_id: int | None = None, user_id: int | None = None
    ) -> List[Comment]:
        offset = (page - 1) * self.items_per_page
        orm_query = select(Comment)

        if post_id:
            orm_query.where(Comment.post_id == post_id)
        if user_id:
            orm_query.where(Comment.author_id == user_id)
        orm_query.offset(offset).limit(self.items_per_page)

        result = await self.session.exec(orm_query)
        comments = result.all()

        return list(comments)

    async def get_comments_by_user(self, user_id: int, page: int) -> List[Comment]:
        offset = (page - 1) * self.items_per_page

        result = await self.session.exec(
            select(Comment)
            .where(Comment.author_id == user_id)
            .offset(offset)
            .limit(self.items_per_page)
        )
        comments = result.all()

        return list(comments)

    async def get_comment(self, comment_id: int) -> Comment | None:
        result = await self.session.exec(
            select(Comment).where(Comment.id == comment_id)
        )
        comment: Comment | None = result.first()

        return comment

    async def edit_comment(self, comment: Comment, content: str | None = None) -> None:
        if content:
            comment.content = content

        self.session.add(comment)
        await self.session.commit()

    async def delete_comment(self, comment: Comment):
        await self.session.delete(comment)
        await self.session.commit()
