from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel, func

from src.domains.user import User


class SaveType(str, Enum):
    GCP = "GCP"
    LOCAL = "LOCAL"


class State(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"


class UseType(str, Enum):
    USER_PROFILE = "USER_PROFILE"


class Image(SQLModel, table=True):  # type: ignore
    id: int | None = Field(primary_key=True)
    name: str
    save_type: SaveType = Field(default=SaveType.LOCAL)
    use_type: UseType = Field(default=UseType.USER_PROFILE)
    state: State = Field(default=State.PENDING)
    created_at: datetime = Field(default=func.now())

    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="images")
