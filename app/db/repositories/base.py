"""Base repository class."""

from typing import TypeVar, Generic, Optional, Type
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Base


T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, model: Type[T], session: AsyncSession):
        """Initialize repository.
        
        Args:
            model: SQLAlchemy model class
            session: Database session
        """
        self.model = model
        self.session = session
    
    async def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            Entity or None if not found
        """
        return await self.session.get(self.model, id)
    
    async def create(self, **kwargs) -> T:
        """Create new entity.
        
        Args:
            **kwargs: Entity attributes
            
        Returns:
            Created entity
        """
        entity = self.model(**kwargs)
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity
    
    async def delete(self, entity: T) -> None:
        """Delete entity.
        
        Args:
            entity: Entity to delete
        """
        await self.session.delete(entity)
        await self.session.commit()
