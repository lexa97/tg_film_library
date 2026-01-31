"""Film service."""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import FilmRepository
from app.db.models import Film
from app.services.base import BaseFilmSearchProvider
from app.services.dto import FilmSearchResult, FilmCreate


logger = logging.getLogger(__name__)


class FilmService:
    """Service for film operations."""
    
    def __init__(
        self, 
        session: AsyncSession,
        search_provider: BaseFilmSearchProvider
    ):
        """Initialize service.
        
        Args:
            session: Database session
            search_provider: Film search provider (e.g., TMDB)
        """
        self.session = session
        self.film_repo = FilmRepository(session)
        self.search_provider = search_provider
    
    async def search_films(
        self, 
        query: str, 
        language: str = "ru"
    ) -> Optional[list[FilmSearchResult]]:
        """Search films using provider.
        
        Args:
            query: Search query
            language: Language code
            
        Returns:
            List of search results, or None if API error occurred
        """
        logger.info(f"Searching films: '{query}' (language: {language})")
        return await self.search_provider.search(query, language)
    
    async def get_or_create_film(self, film_data: FilmCreate) -> Film:
        """Get existing film or create new one.
        
        Args:
            film_data: Film data
            
        Returns:
            Film instance
        """
        # Check if film exists
        existing = await self.film_repo.get_by_external_id(
            external_id=film_data.external_id,
            source=film_data.source
        )
        
        if existing:
            logger.info(f"Film already exists: {film_data.external_id}")
            return existing
        
        # Create new film
        logger.info(f"Creating new film: {film_data.title}")
        return await self.film_repo.create_film(
            external_id=film_data.external_id,
            source=film_data.source,
            title=film_data.title,
            title_original=film_data.title_original,
            year=film_data.year,
            description=film_data.description,
            poster_url=film_data.poster_url
        )
    
    async def get_film_details(
        self,
        external_id: str,
        media_type: str
    ) -> Optional[FilmSearchResult]:
        """Get detailed film information.
        
        Args:
            external_id: External film ID
            media_type: Media type ('movie' or 'tv')
            
        Returns:
            Film details or None
        """
        return await self.search_provider.get_details(external_id, media_type)
