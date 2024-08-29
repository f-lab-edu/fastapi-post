import json
from datetime import datetime, timezone

from fastapi import Cookie, Depends, HTTPException, status
from passlib.context import CryptContext

from src.schemas.auth import SessionContent
from src.servicies.auth import AuthService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    hashed_password: str = pwd_context.hash(secret=plain_password)
    return hashed_password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    valid: bool = pwd_context.verify(secret=plain_password, hash=hashed_password)
    return valid


async def get_current_user(
    session_id: str | None = Cookie(None), service: AuthService = Depends(AuthService)
) -> SessionContent:
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="세션 아이디가 입력되지 않았습니다. 다시 로그인 해 주세요",
        )

    session_result = await service.find_session(session_id)

    if not session_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="존재하지 않는 세션입니다. 다시 로그인 해 주세요",
        )

    session_content_json = json.loads(session_result.session_data)
    session_content = SessionContent(
        id=session_content_json["id"],
        nickname=session_content_json["nickname"],
        role=session_content_json["role"],
        expire=session_content_json["expire"],
    )

    if not session_content.expire:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="세션 만료 기한이 없습니다."
        )

    is_expired = datetime.now(tz=timezone.utc) >= session_content.expire
    if is_expired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="만료된 세션입니다. 다시 로그인 해주세요",
        )
    return session_content
