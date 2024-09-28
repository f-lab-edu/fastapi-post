import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis

from src.auth import get_current_user
from src.database import get_redis
from src.domains.user import Role
from src.schemas.auth import SessionContent
from src.schemas.common import Link
from src.schemas.post import (
    CommentPartial,
    CreatePostRequest,
    CreatePostResponse,
    EditPostRequest,
    EditPostWholeRequest,
    LikePartial,
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

    response = CreatePostResponse(
        id=new_post.id,  # type: ignore
        links=[
            Link(href=f"/posts", rel="self", method="POST"),
            Link(href=f"/posts/{new_post.id}", rel="item", method="GET"),
            Link(href=f"/posts/{new_post.id}", rel="update_partial", method="PATCH"),
            Link(href=f"/posts/{new_post.id}", rel="update_whole", method="PUT"),
            Link(href=f"/posts/{new_post.id}", rel="delete", method="DELETE"),
            Link(href=f"/posts", rel="collection", method="GET"),
            # like? 좋아요는 request객체로 post_id 처리하는데 link에 포함해야하나? 형식은?
            # comments? 댓글도 request객체로 post_id 처리. 마찬가지 문제. create에서 comments까지 안내해야 하나?
        ],
    )

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
                comment=CommentPartial(count=len(post.comments)),
                like=LikePartial(count=len(post.likes)),
                view_count=post.post_view.count,
                links=[
                    Link(href=f"/posts/{post.id}", rel="self", method="GET"),
                    Link(
                        href=f"/posts/{post.id}", rel="update_partial", method="PATCH"
                    ),
                    Link(href=f"/posts/{post.id}", rel="update_whole", method="PUT"),
                    Link(href=f"/posts/{post.id}", rel="delete", method="DELETE"),
                    Link(
                        href=f"/likes/?post_id={post.id}",
                        rel="liked_users",
                        method="GET",
                    ),
                ],
            )
            for post in posts
        ],
        links=[
            Link(href=f"/posts", rel="self", method="GET"),
            Link(href="/posts", rel="create", method="POST"),
        ],
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
        links=[
            Link(href=f"/posts/{post.id}", rel="self", method="GET"),
            Link(href=f"/posts/{post.id}", rel="update_partial", method="PATCH"),
            Link(href=f"/posts/{post.id}", rel="update_whole", method="PUT"),
            Link(href=f"/posts/{post.id}", rel="delete", method="DELETE"),
            Link(href=f"/likes/?post_id={post.id}", rel="liked_users", method="GET"),
            Link(href="/posts", rel="collection", method="GET"),
            Link(href="/posts", rel="create", method="POST"),
            # like? 좋아요 기능을 넣었을 때 게시물에서는 보통 동작해야 할 것 같다
        ],
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

    # 204 상태코드에선 어떻게? 보통 header의 Link에 HATEOAS 구성하면 문제없을 것 같은데 response 객체로 구성했을 때는?
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
    # 204 상태코드

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
    # 204 상태코드

    try:
        await redis.delete(f"post:post_id:{post_id}")
        await redis.delete("posts:*")
    except:
        pass
