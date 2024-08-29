from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///:memory:")


config = Config()
