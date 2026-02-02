"""Test configuration and fixtures."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, User, Group, GroupMember, Film, GroupFilm, Watched


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create test database engine.
    
    Yields:
        AsyncEngine: Test database engine
    """
    # Use in-memory SQLite for tests with StaticPool to keep connection alive
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    """Create test database session.
    
    Args:
        db_engine: Test database engine
        
    Yields:
        AsyncSession: Test database session
    """
    # Create session
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


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
