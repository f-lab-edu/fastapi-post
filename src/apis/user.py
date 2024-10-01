from datetime import datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from ulid import ULID

from src.auth import get_current_user, verify_password
from src.config import config
from src.domains.image import Image, SaveType
from src.schemas.auth import SessionContent
from src.schemas.user import (
    LoginRequest,
    LoginResponse,
    SignUpRequest,
    SignUpResponse,
    UserResponse,
)
from src.servicies.auth import AuthService
from src.servicies.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=SignUpResponse)
async def signup(
    request: SignUpRequest,
    service: UserService = Depends(UserService),
) -> SignUpResponse:
    user = await service.get_user_by_nickname(request.nickname)

    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="이미 가입한 유저입니다"
        )

    new_user = await service.signup_account(
        nickname=request.nickname, password=request.password
    )

    if not new_user.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="유저 생성에 실패했습니다.",
        )

    return SignUpResponse(id=new_user.id, nickname=new_user.nickname)


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    response: Response,
    request: LoginRequest,
    user_service: UserService = Depends(UserService),
    auth_service: AuthService = Depends(AuthService),
    session_id: str | None = Cookie(None),
) -> LoginResponse:
    user = await user_service.get_user_by_nickname(request.nickname)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="존재하지 않는 유저입니다"
        )
    if not verify_password(
        plain_password=request.password, hashed_password=user.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="잘못된 비밀번호입니다"
        )

    session = await auth_service.find_session(session_id)
    new_session_id = (
        session_id
        if (session and session_id)
        else str(ULID.from_datetime(datetime.now()))
    )
    session_value = SessionContent(id=user.id, nickname=user.nickname, role=user.role)  # type: ignore
    await auth_service.insert_session(
        session_id=new_session_id,
        content=session_value,
        expires_delta=timedelta(days=1),
    )
    response.set_cookie(key="session_id", value=new_session_id, httponly=True)

    return LoginResponse(session_id=new_session_id)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    session_id: str | None = Cookie(None),
    auth_service: AuthService = Depends(AuthService),
) -> None:
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="세션 아이디가 없습니다."
        )

    session = await auth_service.find_session(session_id)

    if session:
        await auth_service.delete_session(session)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="존재하지 않는 세션입니다"
        )


@router.get("/profile", status_code=status.HTTP_200_OK)
async def user_profile(
    service: UserService = Depends(UserService),
    current_user: SessionContent = Depends(get_current_user),
) -> UserResponse:
    user_id = current_user.id

    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="존재하지 않는 유저입니다"
        )

    user_image: list[Image] = user.images
    profile_img_url = ""
    if user_image:
        user_type = user_image[0].save_type
        image_name = user_image[0].name
        if user_type == SaveType.GCP:
            profile_img_url = (
                f"{config.GCP_STORAGE_URL}/{config.GCP_BUCKET_NAME}/{image_name}"
            )
        elif user_type == SaveType.LOCAL:
            profile_img_url = f"{image_name}"

    response = UserResponse(
        id=user.id,  # type: ignore
        nickname=user.nickname,
        role=user.role,
        profile_img=profile_img_url,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )

    return response
