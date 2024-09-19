from datetime import datetime
from typing import List

from pydantic import BaseModel


class CreatePostRequest(BaseModel):
    title: str
    content: str


class CreatePostResponse(BaseModel):
    id: int


class PostResponse(BaseModel):
    id: int
    author: str
    title: str
    content: str | None = None
    created_at: datetime
    updated_at: datetime


class PostsResponseBody(BaseModel):
    id: int
    author: str
    title: str
    created_at: datetime
    updated_at: datetime
    comment_count: int
    view_count: int
    like_count: int


class PostsResponse(BaseModel):
    posts: List[PostsResponseBody]


class EditPostRequest(BaseModel):
    title: str | None = None
    content: str | None = None


class EditPostWholeRequest(BaseModel):
    title: str
    content: str
