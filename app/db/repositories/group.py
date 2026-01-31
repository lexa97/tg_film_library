"""Group repository."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Group
from app.db.repositories.base import BaseRepository


class GroupRepository(BaseRepository[Group]):
    """Repository for Group model."""
    
    def __init__(self, session: AsyncSession):
        """Initialize group repository.
        
        Args:
            session: Database session
        """
        super().__init__(Group, session)
    
    async def get_by_admin_id(self, admin_user_id: int) -> Optional[Group]:
        """Get group by admin user ID.
        
        Args:
            admin_user_id: Admin user ID
            
        Returns:
            Group or None if not found
        """
        result = await self.session.execute(
            select(Group).where(Group.admin_user_id == admin_user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_group(self, name: str, admin_user_id: int) -> Group:
        """Create new group.
        
        Args:
            name: Group name
            admin_user_id: Admin user ID
            
        Returns:
            Created group
        """
        return await self.create(name=name, admin_user_id=admin_user_id)
