from datetime import datetime
from enum import Enum
from sqlmodel import (
    Field,
    SQLModel,
    Relationship,
    func,
)


class Role(Enum):
    member = "Member"
    admin = "Admin"


class User(SQLModel, table=True):
    id: int = Field(primary_key=True, index=True)
    nickname: str
    password: str
    role: Role = Field(default=Role.member)
    created_at: datetime = Field(default=func.now())
    updated_at: datetime = Field(default_factory=func.now)

    posts: list["Post"] = Relationship(back_populates="user")

    comments: list["Comment"] = Relationship(back_populates="user")
