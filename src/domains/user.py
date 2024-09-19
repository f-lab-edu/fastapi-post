from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel, func


class Role(Enum):
    member = "Member"
    admin = "Admin"


class User(SQLModel, table=True):  # type: ignore
    id: int | None = Field(primary_key=True)
    nickname: str
    password: str
    role: Role = Field(default=Role.member)
    created_at: datetime = Field(default=func.now())
    updated_at: datetime = Field(default_factory=func.now)

    posts: list["Post"] = Relationship(back_populates="user")  # type: ignore
    comments: list["Comment"] = Relationship(back_populates="user")  # type: ignore
    likes: list["Like"] = Relationship(back_populates="user")  # type: ignore
    notifications: list["Notification"] = Relationship(back_populates="user")  # type: ignore


# like.py에서 User를 참조하는 순환참조 에러 발생.
from src.domains.like import Like
