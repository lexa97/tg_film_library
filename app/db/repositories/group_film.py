"""Group film repository."""

from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import GroupFilm, Film, Watched
from app.db.repositories.base import BaseRepository


class GroupFilmRepository(BaseRepository[GroupFilm]):
    """Repository for GroupFilm model."""
    
    def __init__(self, session: AsyncSession):
        """Initialize group film repository.
        
        Args:
            session: Database session
        """
        super().__init__(GroupFilm, session)
    
    async def get_group_films(
        self,
        group_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> list[GroupFilm]:
        """Get films for a group with pagination.
        
        Args:
            group_id: Group ID
            limit: Maximum number of films to return
            offset: Number of films to skip
            
        Returns:
            List of group films with relations loaded
        """
        result = await self.session.execute(
            select(GroupFilm)
            .where(GroupFilm.group_id == group_id)
            .options(
                selectinload(GroupFilm.film),
                selectinload(GroupFilm.watched)
            )
            .order_by(GroupFilm.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def count_group_films(self, group_id: int) -> int:
        """Count total films in a group.
        
        Args:
            group_id: Group ID
            
        Returns:
            Total number of films
        """
        result = await self.session.execute(
            select(GroupFilm).where(GroupFilm.group_id == group_id)
        )
        return len(list(result.scalars().all()))
    
    async def get_by_film_and_group(
        self,
        film_id: int,
        group_id: int
    ) -> Optional[GroupFilm]:
        """Get group film by film ID and group ID.
        
        Args:
            film_id: Film ID
            group_id: Group ID
            
        Returns:
            GroupFilm or None if not found
        """
        result = await self.session.execute(
            select(GroupFilm)
            .where(
                and_(
                    GroupFilm.film_id == film_id,
                    GroupFilm.group_id == group_id
                )
            )
            .options(
                selectinload(GroupFilm.film),
                selectinload(GroupFilm.watched)
            )
        )
        return result.scalar_one_or_none()
    
    async def add_film_to_group(
        self,
        group_id: int,
        film_id: int,
        added_by_user_id: int
    ) -> GroupFilm:
        """Add film to group.
        
        Args:
            group_id: Group ID
            film_id: Film ID
            added_by_user_id: User ID who added the film
            
        Returns:
            Created group film
        """
        group_film = await self.create(
            group_id=group_id,
            film_id=film_id,
            added_by_user_id=added_by_user_id
        )
        # Reload with relations
        await self.session.refresh(group_film, ["film", "watched"])
        return group_film
    
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
            List of matching group films
        """
        result = await self.session.execute(
            select(GroupFilm)
            .join(Film)
            .where(
                and_(
                    GroupFilm.group_id == group_id,
                    Film.title.ilike(f"%{query}%")
                )
            )
            .options(
                selectinload(GroupFilm.film),
                selectinload(GroupFilm.watched)
            )
        )
        return list(result.scalars().all())
