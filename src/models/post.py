from datetime import datetime
from sqlmodel import (
    Field,
    SQLModel,
    Relationship,
    func,
)
from src.models.user import User


class Post(SQLModel, table=True):
    id: int = Field(primary_key=True, index=True)
    author: str
    title: str
    content: str
    created_at: datetime = Field(default=func.now())

    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="posts")
