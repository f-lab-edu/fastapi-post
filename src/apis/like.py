from fastapi import APIRouter, Depends, HTTPException, status

from src.auth import get_current_user
from src.schemas.auth import SessionContent
from src.schemas.like import CreateLikeRequest, CreateLikeResponse
from src.servicies.like import LikeService, LikeServiceBase
from src.servicies.post import PostService

router = APIRouter(prefix="/likes", tags=["likes"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateLikeResponse,
)
async def create_like(
    request: CreateLikeRequest,
    like_service: LikeServiceBase = Depends(LikeService),
    post_service: PostService = Depends(PostService),
    current_user: SessionContent = Depends(get_current_user),
) -> CreateLikeResponse:
    user_id = current_user.id

    post = await post_service.get_post(request.post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="존재하지 않는 포스트입니다"
        )

    like = await like_service.get_like_by_user_and_post(
        user_id=user_id, post_id=request.post_id
    )
    if like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 좋아요 한 포스트입니다",
        )

    new_like = await like_service.create_like(user_id=user_id, post_id=request.post_id)

    response = CreateLikeResponse(
        id=new_like.id,  # type: ignore
        user_id=new_like.user_id,
        post_id=new_like.post_id,
        created_at=new_like.created_at,
    )

    return response
