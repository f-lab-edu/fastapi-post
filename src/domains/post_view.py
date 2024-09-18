from sqlmodel import Field, Relationship, SQLModel


class PostView(SQLModel, table=True):  # type: ignore
    id: int | None = Field(primary_key=True)
    count: int = Field(default=0)

    post: "Post" = Relationship(back_populates="post_view")  # type: ignore
