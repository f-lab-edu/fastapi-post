from datetime import datetime
from sqlmodel import (
    Field,
    SQLModel,
    Relationship,
    func,
)


class User(SQLModel, table=True):
    id: int = Field(primary_key=True, index=True)
    name: str
    password: str
    created_at: datetime = Field(default=func.now())

    posts: list["Post"] = Relationship(back_populates="user")
