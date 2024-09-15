from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_session


class LikeService:
    def __init__(self, session: AsyncSession = Depends(get_session)) -> None:
        self.session = session
