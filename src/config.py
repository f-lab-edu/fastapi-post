from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///:memory:")
    REDIS_URL: str = Field(default="redis://localhost")


config = Config()
