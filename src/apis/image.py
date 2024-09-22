from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from ulid import ULID

from src.auth import get_current_user
from src.schemas.auth import SessionContent
from src.schemas.image import UploadProfileImgResponse
from src.servicies.image import ImageService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/profile", status_code=status.HTTP_201_CREATED)
async def upload_profile_img(
    file: UploadFile,
    service: ImageService = Depends(ImageService),
    current_user: SessionContent = Depends(get_current_user),
) -> UploadProfileImgResponse:
    user_id = current_user.id

    allow_extension = ["jpg", "jpeg", "png"]
    if not file.content_type or not file.content_type.startswith("image"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미지 파일만 업로드 가능합니다.",
        )
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일 이름이 없습니다.",
        )
    file_extention = file.filename.split(".")[-1].lower()
    if file_extention not in allow_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="업로드 할 수 없는 이미지 확장자입니다. jpg, jpeg, png 확장자를 이용해 주세요",
        )
    content = await file.read()
    filename = f"{str(ULID.from_datetime(datetime.now()))}.{file_extention}"  # uuid로 유니크한 파일명으로 변경

    img_url = await service.save_profile_img(
        user_id=user_id, img_name=filename, img_content=content
    )

    response = UploadProfileImgResponse(img_url=img_url)
    return response
