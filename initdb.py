"""Database initialization script."""

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.config import get_settings
from app.db.models import Base


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_database():
    """Initialize database: create tables if they don't exist."""
    settings = get_settings()
    
    # Создаем движок
    engine = create_async_engine(settings.database_url, echo=False)
    
    try:
        # Создаем все таблицы
        async with engine.begin() as conn:
            logger.info("Checking database schema...")
            
            # Создаем enum тип для ролей если не существует
            await conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE roleenum AS ENUM ('ADMIN', 'MEMBER');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            # Создаем все таблицы из моделей
            await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Database schema is ready!")
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_database())
