"""Film repository."""

from typing import Optional, TYPE_CHECKING

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Film
from app.db.repositories.base import BaseRepository

if TYPE_CHECKING:
    from app.schemas import FilmCreate as FilmCreateSchema


class FilmRepository(BaseRepository[Film]):
    """Repository for Film model."""
    
    def __init__(self, session: AsyncSession):
        """Initialize film repository.
        
        Args:
            session: Database session
        """
        super().__init__(Film, session)
    
    async def get_by_external_id(
        self,
        external_id: str,
        source: str,
        media_type: str = "movie",
    ) -> Optional[Film]:
        """Get film by external ID, source and TMDB media type (movie/tv)."""
        result = await self.session.execute(
            select(Film).where(
                and_(
                    Film.external_id == external_id,
                    Film.source == source,
                    Film.media_type == media_type,
                )
            )
        )
        return result.scalar_one_or_none()

    async def find_by_external(
        self,
        session: AsyncSession,
        external_id: str,
        source: str,
        media_type: str = "movie",
    ) -> Optional[Film]:
        """Совместимость с GroupFilmService: явная сессия транзакции хендлера."""
        result = await session.execute(
            select(Film).where(
                and_(
                    Film.external_id == external_id,
                    Film.source == source,
                    Film.media_type == media_type,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_with_session(
        self, session: AsyncSession, data: "FilmCreateSchema"
    ) -> Film:
        """Создать Film в переданной сессии без commit (для confirm в хендлере)."""
        film = Film(
            external_id=data.external_id,
            source=data.source,
            title=data.title,
            title_original=data.title_original,
            year=data.year,
            description=data.description,
            poster_url=data.poster_url,
            duration=None,
            director=None,
            media_type=data.media_type,
        )
        session.add(film)
        await session.flush()
        return film

    async def create_film(
        self,
        external_id: str,
        source: str,
        title: str,
        title_original: Optional[str] = None,
        year: Optional[int] = None,
        description: Optional[str] = None,
        poster_url: Optional[str] = None,
        duration: Optional[str] = None,
        director: Optional[str] = None,
        media_type: str = "movie",
    ) -> Film:
        """Create new film."""
        return await self.create(
            external_id=external_id,
            source=source,
            title=title,
            title_original=title_original,
            year=year,
            description=description,
            poster_url=poster_url,
            duration=duration,
            director=director,
            media_type=media_type,
        )
