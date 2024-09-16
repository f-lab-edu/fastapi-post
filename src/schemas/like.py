from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from src.domains.user import Role


class CreateLikeRequest(BaseModel):
    post_id: int


class CreateLikeResponse(BaseModel):
    id: int
    user_id: int
    post_id: int
    created_at: datetime


class LikeUserResponse(BaseModel):
    id: int
    nickname: str
    role: Role = Field(default=Role.member)
    created_at: datetime
    updated_at: datetime


class GetLikeUsersResponse(BaseModel):
    users: List[LikeUserResponse]
