import uvicorn
from fastapi import FastAPI

from src.database import db_init
from src.apis.post import router as post_router
from src.apis.user import router as user_router
from src.apis.comment import router as comment_router


app = FastAPI(lifespan=db_init)

app.include_router(router=post_router)
app.include_router(router=user_router)
app.include_router(router=comment_router)


if __name__ == "__main__":
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)
