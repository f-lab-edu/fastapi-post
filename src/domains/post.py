from datetime import datetime
from typing import Optional
from sqlmodel import (
    Field,
    SQLModel,
    Relationship,
    func,
)
from src.domains.user import User


class Post(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    title: str
    content: str
    # default: 정의한 값으로 정적 채우기
    created_at: datetime = Field(default=func.now())
    # default_factory: 정의한 함수를 해당 시점에 호출해서 채우기
    updated_at: datetime = Field(default_factory=func.now)

    author_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="posts")

    comments: list["Comment"] = Relationship(back_populates="post")

    @property
    def author(self):
        return self._author

    @author.setter
    def author(self, author):
        self._author = author

    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        data["author"] = self.author
        return data