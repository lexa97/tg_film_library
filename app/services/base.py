"""Base classes for services."""

from abc import ABC, abstractmethod
from typing import Optional

from app.services.dto import FilmSearchResult


class BaseFilmSearchProvider(ABC):
    """Abstract base class for film search providers."""
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        language: str = "ru"
    ) -> Optional[list[FilmSearchResult]]:
        """Search films by query.
        
        Args:
            query: Search query (film title)
            language: Language code (e.g., 'ru', 'en')
            
        Returns:
            List of search results (up to 5), or None if API error occurred
        """
        pass
    
    @abstractmethod
    async def get_details(
        self,
        external_id: str,
        media_type: str
    ) -> Optional[FilmSearchResult]:
        """Get detailed information about a film.
        
        Args:
            external_id: External film ID
            media_type: Media type ('movie' or 'tv')
            
        Returns:
            Film details or None if not found
        """
        pass
