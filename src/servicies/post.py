from typing import List, Tuple

from fastapi import Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_session
from src.domains.post import Post
from src.domains.user import User


class PostService:
    def __init__(self, session: AsyncSession = Depends(get_session)) -> None:
        self.session = session
        self.items_per_page = 20

    async def create_post(self, user_id: int, title: str, content: str) -> Post:
        new_post = Post(author_id=user_id, title=title, content=content)

        self.session.add(new_post)
        await self.session.commit()
        await self.session.refresh(new_post)

        return new_post

    async def get_posts(self, page: int) -> List[Post]:
        offset = (page - 1) * self.items_per_page
        result = await self.session.exec(
            select(Post, User.nickname)
            .join(User)
            .offset(offset)
            .limit(self.items_per_page)
        )
        posts = result.all()
        """
        목록 -> 단순히 목록만 보여줄 뿐인데 조인까지 타야하나? 20개면 조인이 최소 20회 일어나는데?
        작성자까지 포스트에 넣어둔다면? 유저와 작성자 내용이 중복된다 -> 트레이드 오프의 관계일까 
        """

        author_include_posts: list[Post] = []
        for post, author in posts:
            post.author = author
            author_include_posts.append(post)

        return author_include_posts

    async def get_post(self, post_id: int) -> Post | None:
        result = await self.session.exec(
            select(Post, User).join(User).where(Post.id == post_id)
        )

        result_data: Tuple[Post, User] | None = result.first()
        if not result_data:
            return None

        post, user = result_data
        post.user = user
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

    async def delete_post(self, post: Post):
        await self.session.delete(post)
        await self.session.commit()
