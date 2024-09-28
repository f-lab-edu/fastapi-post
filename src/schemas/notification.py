from datetime import datetime

from pydantic import BaseModel


class NotificationResponseBody(BaseModel):
    id: int
    user_id: int
    post_id: int
    created_at: datetime


class GetNotificationsResponse(BaseModel):
    notifications: list[NotificationResponseBody]
