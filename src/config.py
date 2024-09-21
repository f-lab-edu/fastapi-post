from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    # TODO: 아래 변수 값이 DATABASE_URL 환경 변수를 읽어 오나요? 잘 읽어오는지 확인해보고 수정할 부분 있으면 수정해보세요.
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///:memory:")
    REDIS_URL: str = Field(default="redis://localhost")
    UPLOAD_DIR: str = Field(default="./profile_img")


config = Config()
