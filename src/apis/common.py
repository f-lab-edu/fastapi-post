from fastapi import APIRouter, status

router = APIRouter(tags=["common"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
)
async def health() -> None:
    """
    health check
    """
    return
