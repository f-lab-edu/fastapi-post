import time

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.config import config
from src.database import redis
from src.schemas.common import Bucket


# 토큰 버킷 알고리즘
class BucketRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not request.client:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "요청에 client 속성이 없습니다."},
            )
        client_ip = request.client.host
        current_time = time.time()
        bucket_key = f"bucket:{client_ip}"
        bucket_data = await redis.hgetall(bucket_key)
        if not bucket_data:
            bucket = Bucket(tokens=config.BUCKET_SIZE, last_refill=current_time)
        else:
            bucket = Bucket.model_validate(bucket_data)
        time_passed = current_time - bucket.last_refill

        # 정수로 계산하기 위해 형변환
        refill_amount = int(time_passed * (config.REQUESTS_PER_MINUTE / 60))
        bucket.tokens = min(bucket.tokens + refill_amount, config.BUCKET_SIZE)
        bucket.last_refill = current_time

        retry_after = max(
            0, int((1 - bucket.tokens) / (config.REQUESTS_PER_MINUTE / 60))
        )
        if bucket.tokens < 1:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "처리율 제한을 초과하였습니다. 나중에 다시 시도해주세요"
                },
                headers={
                    "X-Ratelimit-Retry-After": str(retry_after),
                    "X-Ratelimit-Remaining": str(bucket.tokens),
                    "X-Ratelimit-Limit": str(config.BUCKET_SIZE),
                },
            )
        await redis.hset(bucket_key, "tokens", bucket.tokens - 1)
        await redis.hset(bucket_key, "last_refill", current_time)
        response: Response = await call_next(request)

        # 처리율 제한 헤더
        response.headers.append(key="X-Ratelimit-Remaining", value=str(bucket.tokens))
        response.headers.append(key="X-Ratelimit-Limit", value=str(config.BUCKET_SIZE))
        response.headers.append(key="X-Ratelimit-Retry-After", value=str(retry_after))

        return response
