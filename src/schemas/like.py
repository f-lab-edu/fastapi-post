from datetime import datetime

from pydantic import BaseModel


class CreateLikeRequest(BaseModel):
    post_id: int


class CreateLikeResponse(BaseModel):
    id: int
    user_id: int
    post_id: int
    created_at: datetime
