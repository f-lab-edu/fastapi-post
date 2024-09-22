import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis

from src.auth import get_current_user
from src.database import get_redis
from src.domains.user import Role
from src.schemas.auth import SessionContent
from src.schemas.post import (
    CreatePostRequest,
    CreatePostResponse,
    EditPostRequest,
    EditPostWholeRequest,
    PostResponse,
    PostsResponse,
    PostsResponseBody,
)
from src.servicies.post import PostService

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=CreatePostResponse
)
async def create_post(
    request: CreatePostRequest,
    service: PostService = Depends(PostService),
    redis: Redis = Depends(get_redis),
    current_user: SessionContent = Depends(get_current_user),
) -> CreatePostResponse:
    user_id = current_user.id

    new_post = await service.create_post(
        user_id=user_id, title=request.title, content=request.content
    )

    response = CreatePostResponse(id=new_post.id)  # type: ignore

    try:
        await redis.delete("posts:*")
    except:
        pass

    return response


@router.get("/", response_model=PostsResponse, status_code=status.HTTP_200_OK)
async def get_posts(
    page: int = Query(1),
    service: PostService = Depends(PostService),
    redis: Redis = Depends(get_redis),
) -> PostsResponse:
    cache_key = f"posts:page:{page}"
    try:
        cached_data = await redis.get(cache_key)
        if cached_data:
            return PostsResponse(**json.loads(cached_data))
    except:
        pass

    posts = await service.get_posts(page)

    response = PostsResponse(
        posts=[
            PostsResponseBody(
                id=post.id,  # type: ignore
                author=post.user.nickname,
                title=post.title,
                created_at=post.created_at,
                updated_at=post.updated_at,
                comment_count=len(post.comments),
                like_count=len(post.likes),
                view_count=post.post_view.count,
            )
            for post in posts
        ]
    )
    try:
        await redis.setex(
            name=cache_key, time=3600, value=json.dumps(response.model_dump())
        )
    except:
        pass

    return response


@router.get("/{post_id}", response_model=PostResponse, status_code=status.HTTP_200_OK)
async def get_post(
    post_id: int,
    service: PostService = Depends(PostService),
    redis: Redis = Depends(get_redis),
) -> PostResponse:
    cache_key = f"post:post_id:{post_id}"
    try:
        cached_data = await redis.get(cache_key)
        if cached_data:
            return PostResponse(**json.loads(cached_data))
    except:
        pass

    post = await service.get_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="존재하지 않는 포스트입니다"
        )

    response = PostResponse(
        id=post.id,  # type: ignore
        author=post.user.nickname,
        title=post.title,
        content=post.content,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )
    await service.increase_post_view(post_id=post.id)  # type: ignore

    try:
        await redis.setex(
            name=cache_key, time=3600, value=json.dumps(response.model_dump())
        )
    except:
        pass

    return response


@router.patch("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def edit_post(
    post_id: int,
    request: EditPostRequest,
    service: PostService = Depends(PostService),
    redis: Redis = Depends(get_redis),
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

    try:
        await redis.delete(f"post:post_id:{post_id}")
        await redis.delete("posts:*")
    except:
        pass


@router.put("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def edit_post_whole(
    post_id: int,
    request: EditPostWholeRequest,
    service: PostService = Depends(PostService),
    redis: Redis = Depends(get_redis),
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

    try:
        await redis.delete(f"post:post_id:{post_id}")
        await redis.delete("posts:*")
    except:
        pass


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    service: PostService = Depends(PostService),
    redis: Redis = Depends(get_redis),
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

    try:
        await redis.delete(f"post:post_id:{post_id}")
        await redis.delete("posts:*")
    except:
        pass
