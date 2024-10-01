from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///:memory:")
    REDIS_URL: str = Field(default="redis://localhost")
    LOCAL_UPLOAD_DIR: str = Field(default="./profile_img")
    GOOGLE_APPLICATION_CREDENTIALS: str = Field(default="")
    GCP_STORAGE_URL: str = Field(default="https://storage.googleapis.com")
    GCP_BUCKET_NAME: str = Field(default="fastapi-post-storage")

    # bucket rate limit
    REQUESTS_PER_MINUTE: int = 60
    BUCKET_SIZE: float = 10.0


config = Config()
