from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel, func


class Role(Enum):
    member = "Member"
    admin = "Admin"


class Notification(SQLModel, table=True):  # type: ignore
    id: int | None = Field(primary_key=True)
    created_at: datetime = Field(default=func.now())

    user_id: int = Field(foreign_key="user.id")
    user: "User" = Relationship(back_populates="notifications")  # type: ignore

    post_id: int = Field(foreign_key="post.id")
    post: "Post" = Relationship(back_populates="notifications")  # type: ignore
