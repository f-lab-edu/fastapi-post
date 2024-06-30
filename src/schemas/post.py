from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Post(BaseModel):
    id: Optional[int] = None
    author: Optional[str] = None
    title: str
    content: str
    created_at: Optional[datetime] = None


class EditPost(BaseModel):
    title: str
    content: str
