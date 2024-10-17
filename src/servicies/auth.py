import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_session_factory
from src.domains.login_session import LoginSession
from src.schemas.auth import SessionContent


class AuthService:
    def __init__(
        self, session_factory: AsyncSession = Depends(get_session_factory)
    ) -> None:
        self.session_factory = session_factory

    async def find_session(self, session_id: str | None = None) -> LoginSession | None:
        if not session_id:
            return None

        sharding_key = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
        async with self.session_factory(sharding_key) as session:  # type: ignore
            result = await session.exec(
                select(LoginSession).where(LoginSession.id == session_id)
            )

            result_data: LoginSession | None = result.first()
            if not result_data:
                return None

            return result_data

    async def insert_session(
        self, session_id: str, content: SessionContent, expires_delta: timedelta
    ) -> str:
        expire = datetime.now(tz=timezone.utc) + expires_delta
        content.expire = expire

        new_login_session = LoginSession(
            id=session_id, session_data=content.model_dump_json()
        )
        sharding_key = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
        async with self.session_factory(sharding_key) as session:  # type: ignore
            session.add(new_login_session)
            await session.commit()

        return session_id

    async def delete_session(self, login_session: LoginSession) -> None:
        sharding_key = int(hashlib.md5(login_session.id.encode()).hexdigest(), 16)  # type: ignore
        async with self.session_factory(sharding_key) as session:  # type: ignore
            await session.delete(login_session)
            await session.commit()
