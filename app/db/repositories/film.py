"""Film repository."""

from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Film
from app.db.repositories.base import BaseRepository


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
        source: str
    ) -> Optional[Film]:
        """Get film by external ID and source.
        
        Args:
            external_id: External film ID (e.g., TMDB ID)
            source: Source name (e.g., 'tmdb')
            
        Returns:
            Film or None if not found
        """
        result = await self.session.execute(
            select(Film).where(
                and_(
                    Film.external_id == external_id,
                    Film.source == source
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def create_film(
        self,
        external_id: str,
        source: str,
        title: str,
        title_original: Optional[str] = None,
        year: Optional[int] = None,
        description: Optional[str] = None,
        poster_url: Optional[str] = None
    ) -> Film:
        """Create new film.
        
        Args:
            external_id: External film ID
            source: Source name
            title: Film title
            title_original: Original title
            year: Release year
            description: Film description
            poster_url: Poster URL
            
        Returns:
            Created film
        """
        return await self.create(
            external_id=external_id,
            source=source,
            title=title,
            title_original=title_original,
            year=year,
            description=description,
            poster_url=poster_url
        )
