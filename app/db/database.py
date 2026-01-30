from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base

# Для Alembic нужен sync URL без +asyncpg при создании миграций — используем echo=False в engine
def get_engine(database_url: str, echo: bool = False):
    return create_async_engine(
        database_url,
        echo=echo,
        pool_pre_ping=True,
    )


async_session_maker: async_sessionmaker[AsyncSession] | None = None


async def init_db(database_url: str) -> None:
    global async_session_maker
    engine = get_engine(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
