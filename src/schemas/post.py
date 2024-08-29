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


class PostsResponse(BaseModel):
    posts: List[PostResponse]


class EditPostRequest(BaseModel):
    title: str | None = None
    content: str | None = None


class EditPostWholeRequest(BaseModel):
    title: str
    content: str
