import re
from datetime import datetime
from typing import List

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, field_validator

from src.domains.user import Role


class SignUpRequest(BaseModel):
    nickname: str
    password: str = Field(
        min_length=8,
        description="비밀번호는 8자 이상, 대문자 1자리 이상 포함",
    )
    role: Role = Field(default=Role.member)

    @field_validator("password", mode="after")
    @classmethod
    def check_uppercase(cls, v):
        if not re.search(r"[A-Z]", v):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="문자열에 대문자가 하나 이상 포함되어야 합니다",
            )
        return v


class SignUpResponse(BaseModel):
    id: int
    nickname: str


class LoginRequest(BaseModel):
    nickname: str
    password: str


class LoginResponse(BaseModel):
    session_id: str


class NotificationsResponseBody(BaseModel):
    id: int
    user_id: int
    post_id: int


class NotificationsResponse(BaseModel):
    notifications: List[NotificationsResponseBody]


class UserResponse(BaseModel):
    id: int
    nickname: str
    role: Role = Field(default=Role.member)
    profile_img: str
    created_at: datetime
    updated_at: datetime


class UploadProfileImgResponse(BaseModel):
    img_url: str
