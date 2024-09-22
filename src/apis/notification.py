from fastapi import APIRouter, Depends, status

from src.auth import get_current_user
from src.schemas.auth import SessionContent
from src.schemas.notification import GetNotificationsResponse, NotificationResponseBody
from src.servicies.notification import NotificationService, NotificationServiceBase

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get(
    "/", response_model=GetNotificationsResponse, status_code=status.HTTP_200_OK
)
async def get_notifications(
    service: NotificationServiceBase = Depends(NotificationService),
    current_user: SessionContent = Depends(get_current_user),
) -> GetNotificationsResponse:
    user_id = current_user.id

    notifications = await service.get_notifications_by_user_id(user_id=user_id)

    response = GetNotificationsResponse(
        notifications=[
            NotificationResponseBody(
                id=notification.id,  # type: ignore
                user_id=notification.actor_user_id,
                post_id=notification.post_id,
                created_at=notification.created_at,
            )
            for notification in notifications
        ]
    )

    return response
