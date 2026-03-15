from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.db.base_class import Base

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        from app.models import models
        await conn.run_sync(Base.metadata.create_all)