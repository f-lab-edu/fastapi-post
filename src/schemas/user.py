from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    id: Optional[int] = None
    name: str
    password: str
    created_at: Optional[datetime] = None


class Login(BaseModel):
    name: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
