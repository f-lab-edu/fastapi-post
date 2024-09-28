from pydantic import BaseModel


class Link(BaseModel):
    href: str
    rel: str
    method: str
