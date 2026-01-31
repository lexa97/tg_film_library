"""Group film service."""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import GroupFilmRepository, WatchedRepository
from app.db.models import GroupFilm, Film
from app.services.dto import FilmCreate
from app.services.film import FilmService


logger = logging.getLogger(__name__)


class GroupFilmService:
    """Service for group film operations."""
    
    def __init__(
        self,
        session: AsyncSession,
        film_service: FilmService
    ):
        """Initialize service.
        
        Args:
            session: Database session
            film_service: Film service
        """
        self.session = session
        self.group_film_repo = GroupFilmRepository(session)
        self.watched_repo = WatchedRepository(session)
        self.film_service = film_service
    
    async def add_film_to_group(
        self,
        group_id: int,
        film_data: FilmCreate,
        added_by_user_id: int
    ) -> GroupFilm:
        """Add film to group's list.
        
        Args:
            group_id: Group ID
            film_data: Film data
            added_by_user_id: User ID who added the film
            
        Returns:
            Created group film
            
        Raises:
            ValueError: If film already in group
        """
        # Get or create film
        film = await self.film_service.get_or_create_film(film_data)
        
        # Check if already in group
        existing = await self.group_film_repo.get_by_film_and_group(
            film_id=film.id,
            group_id=group_id
        )
        if existing:
            raise ValueError("Film is already in the group's list")
        
        # Add to group
        logger.info(f"Adding film {film.id} to group {group_id}")
        return await self.group_film_repo.add_film_to_group(
            group_id=group_id,
            film_id=film.id,
            added_by_user_id=added_by_user_id
        )
    
    async def get_group_films(
        self,
        group_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> tuple[list[GroupFilm], int]:
        """Get group's films with pagination.
        
        Args:
            group_id: Group ID
            limit: Max number of films to return
            offset: Number of films to skip
            
        Returns:
            Tuple of (films list, total count)
        """
        films = await self.group_film_repo.get_group_films(
            group_id=group_id,
            limit=limit,
            offset=offset
        )
        total = await self.group_film_repo.count_group_films(group_id)
        
        return films, total
    
    async def search_in_group(
        self,
        group_id: int,
        query: str
    ) -> list[GroupFilm]:
        """Search films in group by title.
        
        Args:
            group_id: Group ID
            query: Search query
            
        Returns:
            List of matching films
        """
        return await self.group_film_repo.search_in_group(group_id, query)
    
    async def mark_watched(
        self,
        group_film_id: int,
        marked_by_user_id: int
    ) -> None:
        """Mark film as watched for the group.
        
        Args:
            group_film_id: Group film ID
            marked_by_user_id: User ID who marked as watched
            
        Raises:
            ValueError: If already marked as watched
        """
        # Check if already watched
        existing = await self.watched_repo.get_by_group_film(group_film_id)
        if existing:
            raise ValueError("Film is already marked as watched")
        
        # Mark as watched
        logger.info(f"Marking group film {group_film_id} as watched")
        await self.watched_repo.mark_watched(
            group_film_id=group_film_id,
            marked_by_user_id=marked_by_user_id
        )
    
    async def is_watched(self, group_film_id: int) -> bool:
        """Check if film is marked as watched.
        
        Args:
            group_film_id: Group film ID
            
        Returns:
            True if watched
        """
        watched = await self.watched_repo.get_by_group_film(group_film_id)
        return watched is not None
    
    async def get_group_film_by_id(self, group_film_id: int) -> Optional[GroupFilm]:
        """Get group film by ID.
        
        Args:
            group_film_id: Group film ID
            
        Returns:
            GroupFilm or None
        """
        return await self.group_film_repo.get_by_id(group_film_id)
