from datetime import datetime
from typing import List

from pydantic import BaseModel


class CreateCommentRequest(BaseModel):
    post_id: int
    content: str


class CreateCommentResponse(BaseModel):
    id: int
    post_id: int
    author_id: int
    content: str
    created_at: datetime
    updated_at: datetime


class CommentResponse(BaseModel):
    id: int
    post_id: int
    author_id: int
    content: str
    created_at: datetime
    updated_at: datetime


class CommentsResponse(BaseModel):
    comments: List[CommentResponse]


class EditComment(BaseModel):
    content: str | None = None
