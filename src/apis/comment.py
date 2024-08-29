from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.auth import get_current_user
from src.domains.user import Role
from src.schemas.auth import SessionContent
from src.schemas.comment import (
    CommentResponse,
    CommentsResponse,
    CreateCommentRequest,
    CreateCommentResponse,
    EditComment,
)
from src.servicies.comment import CommentService
from src.servicies.post import PostService

router = APIRouter(prefix="/comments", tags=["comments"])


# post_id로 바로 부르는건 햇갈릴거 같다. commets/1이 1번 코멘트가 아니라 post1에 코멘트 다는 거라고 직관적으로 모름
# POST /comments?post_id=1 이게 나을듯
# POST /comments/list?post_id=1
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateCommentResponse,
)
async def create_comment(
    request: CreateCommentRequest,
    comment_service: CommentService = Depends(CommentService),
    post_service: PostService = Depends(PostService),
    current_user: SessionContent = Depends(get_current_user),
) -> CreateCommentResponse:
    user_id = current_user.id

    post = await post_service.get_post(request.post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="존재하지 않는 포스트입니다"
        )

    new_comment = await comment_service.create_comment(
        user_id=user_id, post_id=request.post_id, content=request.content
    )

    if not new_comment.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="코멘트 생성에 실패했습니다.",
        )

    return CreateCommentResponse(
        id=new_comment.id,
        author_id=new_comment.author_id,
        post_id=new_comment.post_id,
        content=new_comment.content,
        created_at=new_comment.created_at,
        updated_at=new_comment.updated_at,
    )


@router.get(
    "/",
    response_model=CommentsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_comments(
    post_id: int | None = None,
    user_id: int | None = None,
    page: int = Query(1),
    service: CommentService = Depends(CommentService),
) -> CommentsResponse:
    comments = await service.get_comments(post_id=post_id, user_id=user_id, page=page)

    return CommentsResponse(
        comments=[
            CommentResponse(
                id=comment.id,  # type: ignore
                post_id=comment.post_id,
                author_id=comment.author_id,
                content=comment.content,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
            )
            for comment in comments
        ]
    )


@router.patch("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def edit_comment(
    comment_id: int,
    request: EditComment,
    service: CommentService = Depends(CommentService),
    current_user: SessionContent = Depends(get_current_user),
) -> None:
    user_id = current_user.id
    user_role = current_user.role

    comment = await service.get_comment(comment_id)

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="존재하지 않는 코멘트입니다"
        )

    if (not comment.author_id == user_id) and (not user_role == Role.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="작성자 또는 관리자만 수정할 수 있습니다",
        )

    await service.edit_comment(comment=comment, content=request.content)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    service: CommentService = Depends(CommentService),
    current_user: SessionContent = Depends(get_current_user),
) -> None:
    user_id = current_user.id
    user_role = current_user.role

    comment = await service.get_comment(comment_id)

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="존재하지 않는 코멘트입니다"
        )

    if (not comment.author_id == user_id) and (not user_role == Role.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="작성자 또는 관리자만 삭제할 수 있습니다",
        )

    await service.delete_comment(comment)
