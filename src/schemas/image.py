from pydantic import BaseModel


class UploadProfileImgResponse(BaseModel):
    img_url: str
