from datetime import datetime, timedelta, timezone
from typing import Dict, Union

from jose import jwt
from passlib.context import CryptContext

from src.config import Settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def encode_access_token(data: dict, expires_delta: timedelta) -> dict:
    expire = datetime.now(tz=timezone.utc) + expires_delta
    payload = {"exp": expire, "data": data}
    encoded_jwt = jwt.encode(
        claims=payload, key=Settings.JWT_SECRET_KEY, algorithm=Settings.JWT_ALGORITHM
    )
    return {"access_token": encoded_jwt}


def decode_access_token(token) -> Dict[str, Union[str, int]]:
    decoded_jwt = jwt.decode(
        token, key=Settings.JWT_SECRET_KEY, algorithms=Settings.JWT_ALGORITHM
    )
    return decoded_jwt


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(secret=plain_password)


def verify_password(plain_password: str) -> bool:
    hashed_password = hash_password(plain_password)
    return pwd_context.verify(secret=plain_password, hash=hashed_password)
