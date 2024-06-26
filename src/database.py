from sqlalchemy.orm import sessionmaker, as_declarative, declared_attr
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession


DATABASE_URL="sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, echo=True)


AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False, 
    bind=engine,
    class_=AsyncSession,
    )


@as_declarative()
class Base:
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__tablename__.lower()

    @classmethod
    async def get_db(cls):
        async with AsyncSessionLocal() as session:
            yield session