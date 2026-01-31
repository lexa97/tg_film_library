"""Watched repository."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Watched
from app.db.repositories.base import BaseRepository


class WatchedRepository(BaseRepository[Watched]):
    """Repository for Watched model."""
    
    def __init__(self, session: AsyncSession):
        """Initialize watched repository.
        
        Args:
            session: Database session
        """
        super().__init__(Watched, session)
    
    async def get_by_group_film(self, group_film_id: int) -> Optional[Watched]:
        """Get watched status by group film ID.
        
        Args:
            group_film_id: Group film ID
            
        Returns:
            Watched or None if not found
        """
        result = await self.session.execute(
            select(Watched).where(Watched.group_film_id == group_film_id)
        )
        return result.scalar_one_or_none()
    
    async def mark_watched(
        self,
        group_film_id: int,
        marked_by_user_id: int
    ) -> Watched:
        """Mark film as watched.
        
        Args:
            group_film_id: Group film ID
            marked_by_user_id: User ID who marked as watched
            
        Returns:
            Created watched record
        """
        return await self.create(
            group_film_id=group_film_id,
            marked_by_user_id=marked_by_user_id
        )
