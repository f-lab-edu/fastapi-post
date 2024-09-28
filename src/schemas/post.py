from datetime import datetime
from typing import List

from pydantic import BaseModel

from src.schemas.common import Link


class CreatePostRequest(BaseModel):
    title: str
    content: str


class CreatePostResponse(BaseModel):
    id: int
    # hateos
    links: list[Link]


class PostResponse(BaseModel):
    id: int
    author: str
    title: str
    content: str | None = None
    created_at: datetime
    updated_at: datetime
    # hateos
    links: list[Link]


class LikePartial(BaseModel):
    count: int


class CommentPartial(BaseModel):
    count: int


class PostsResponseBody(BaseModel):
    id: int
    author: str
    title: str
    created_at: datetime
    updated_at: datetime
    view_count: int
    comment: CommentPartial
    like: LikePartial
    links: list[Link]


class PostsResponse(BaseModel):
    posts: List[PostsResponseBody]
    # hateos
    links: list[Link]


class EditPostRequest(BaseModel):
    title: str | None = None
    content: str | None = None


class EditPostWholeRequest(BaseModel):
    title: str
    content: str
