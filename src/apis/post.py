from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.auth import get_current_user
from src.domains.user import Role
from src.schemas.auth import SessionContent
from src.schemas.post import (
    CreatePostRequest,
    CreatePostResponse,
    EditPostRequest,
    EditPostWholeRequest,
    PostResponse,
    PostsResponse,
)
from src.servicies.post import PostService

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=CreatePostResponse
)
async def create_post(
    request: CreatePostRequest,
    service: PostService = Depends(PostService),
    current_user: SessionContent = Depends(get_current_user),
) -> CreatePostResponse:
    user_id = current_user.id

    new_post = await service.create_post(
        user_id=user_id, title=request.title, content=request.content
    )

    if not new_post.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="포스트 생성에 실패했습니다.",
        )

    return CreatePostResponse(id=new_post.id)


@router.get("/", response_model=PostsResponse, status_code=status.HTTP_200_OK)
async def get_get_posts(
    page: int = Query(1), service: PostService = Depends(PostService)
) -> PostsResponse:
    posts = await service.get_posts(page)

    return PostsResponse(
        posts=[
            PostResponse(
                id=post.id,  # type: ignore
                author=post.author,
                title=post.title,
                content=post.content,
                created_at=post.created_at,
                updated_at=post.updated_at,
            )
            for post in posts
        ]
    )


@router.get("/{post_id}", response_model=PostResponse, status_code=status.HTTP_200_OK)
async def get_post(
    post_id: int, service: PostService = Depends(PostService)
) -> PostResponse:
    post = await service.get_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="존재하지 않는 포스트입니다"
        )

    if not post.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="포스트 생성에 실패했습니다.",
        )

    return PostResponse(
        id=post.id,
        author=post.user.nickname,
        title=post.title,
        content=post.content,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.patch("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def edit_post(
    post_id: int,
    request: EditPostRequest,
    service: PostService = Depends(PostService),
    current_user: SessionContent = Depends(get_current_user),
) -> None:
    user_id = current_user.id
    user_role = current_user.role

    post = await service.get_post(post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="존재하지 않는 포스트입니다"
        )

    if (not post.author_id == user_id) and (not user_role == Role.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="작성자 또는 관리자만 수정할 수 있습니다",
        )

    await service.edit_post(post=post, title=request.title, content=request.content)


@router.put("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def edit_post_whole(
    post_id: int,
    request: EditPostWholeRequest,
    service: PostService = Depends(PostService),
    current_user: SessionContent = Depends(get_current_user),
) -> None:
    user_id = current_user.id
    user_role = current_user.role

    post = await service.get_post(post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="존재하지 않는 포스트입니다"
        )

    if (not post.author_id == user_id) and (not user_role == Role.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="작성자 또는 관리자만 수정할 수 있습니다",
        )

    await service.edit_post(post=post, title=request.title, content=request.content)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    service: PostService = Depends(PostService),
    current_user: SessionContent = Depends(get_current_user),
) -> None:
    user_id = current_user.id
    user_role = current_user.role

    post = await service.get_post(post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="존재하지 않는 포스트입니다"
        )

    if (not post.author_id == user_id) and (not user_role == Role.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="작성자 또는 관리자만 삭제할 수 있습니다",
        )

    await service.delete_post(post)
