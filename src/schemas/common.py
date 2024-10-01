from pydantic import BaseModel


class Link(BaseModel):
    href: str
    rel: str
    method: str


class Bucket(BaseModel):
    tokens: float
    last_refill: float


class EditRateLimitRequest(BaseModel):
    requests_per_minute: int | None = None
    bucket_size: int | None = None
