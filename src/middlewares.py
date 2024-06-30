from fastapi import Request, status
from fastapi.responses import JSONResponse
from functools import wraps

from src.auth import decode_access_token


def jwt_middleware(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        cookies = request.cookies
        if "access_token" in cookies.keys():
            access_token = cookies.get("access_token")
            decoded_token = decode_access_token(access_token)
            request.state.user = decoded_token["data"]
            return await func(request, *args, **kwargs)

        return JSONResponse(
            {"detail": "Token is required"}, status_code=status.HTTP_401_UNAUTHORIZED
        )

    return wrapper
