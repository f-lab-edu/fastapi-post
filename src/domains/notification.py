from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel, func


class Role(Enum):
    member = "Member"
    admin = "Admin"


class Notification(SQLModel, table=True):  # type: ignore
    id: int | None = Field(primary_key=True)
    created_at: datetime = Field(default=func.now())

    # 포스트 작성자 유저
    target_user_id: int = Field(foreign_key="user.id")
    target_user: "User" = Relationship(  # type: ignore
        back_populates="target_notifications",
        sa_relationship_kwargs={"foreign_keys": "Notification.target_user_id"},
    )

    # 포스트에 좋아요한 유저
    actor_user_id: int = Field(foreign_key="user.id")
    actor_user: "User" = Relationship(  # type: ignore
        back_populates="actor_notifications",
        sa_relationship_kwargs={"foreign_keys": "Notification.actor_user_id"},
    )

    post_id: int = Field(foreign_key="post.id")
    post: "Post" = Relationship(back_populates="notifications")  # type: ignore
