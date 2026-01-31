"""Test configuration and fixtures."""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.db.models import Base


@pytest.fixture
async def db_session():
    """Create test database session.
    
    Yields:
        AsyncSession: Test database session
    """
    # Use in-memory SQLite for tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=NullPool,
        echo=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
def mock_tmdb_search_results():
    """Mock TMDB search results."""
    from app.services.dto import FilmSearchResult
    
    return [
        FilmSearchResult(
            external_id="550",
            source="tmdb",
            title="Бойцовский клуб",
            title_original="Fight Club",
            year=1999,
            description="Сотрудник страховой компании страдает хронической бессонницей...",
            poster_url="https://image.tmdb.org/t/p/w500/test.jpg",
            media_type="movie"
        )
    ]
