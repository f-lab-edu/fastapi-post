from datetime import datetime

from sqlmodel import Field, SQLModel, func


class LoginSession(SQLModel, table=True):  # type: ignore
    id: str | None = Field(primary_key=True)
    session_data: str
    created_at: datetime = Field(default=func.now())
