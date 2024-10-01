from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel, func


class Role(str, Enum):
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
    target_notifications: list["Notification"] = Relationship(  # type: ignore
        back_populates="target_user",
        sa_relationship_kwargs={"foreign_keys": "Notification.target_user_id"},
    )
    actor_notifications: list["Notification"] = Relationship(  # type: ignore
        back_populates="actor_user",
        sa_relationship_kwargs={"foreign_keys": "Notification.actor_user_id"},
    )
    images: list["Image"] = Relationship(back_populates="user")  # type: ignore


from src.domains.like import Like
