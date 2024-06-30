from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_session
from src.models.user import User as UserModel
from src.auth import encode_access_token, hash_password, verify_password
from src.schemas.user import User, Login, LoginResponse


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def signup(
    signup_user: User, session: AsyncSession = Depends(get_session)
) -> int:
    """
    return signup user id
    """
    hashed_password = hash_password(plain_password=signup_user.password)
    new_user = UserModel(name=signup_user.name, password=hashed_password)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return new_user.id


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    response: Response, login_user: Login, session: AsyncSession = Depends(get_session)
) -> LoginResponse:
    result = await session.exec(
        select(UserModel).where(UserModel.name == login_user.name)
    )
    user = result.one()

    if not user:
        raise HTTPException(status_code=400, detail="User not exists")

    if not verify_password(user.password):
        raise HTTPException(status_code=400, detail="Invalid password")

    token_value = {"id": user.id, "name": user.name}
    access_token = encode_access_token(token_value, timedelta(hours=1))
    response.set_cookie(
        key="access_token", value=access_token.get("access_token"), httponly=True
    )

    return access_token
