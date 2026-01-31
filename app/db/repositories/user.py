"""User repository."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model."""
    
    def __init__(self, session: AsyncSession):
        """Initialize user repository.
        
        Args:
            session: Database session
        """
        super().__init__(User, session)
    
    async def get_by_telegram_id(self, telegram_user_id: int) -> Optional[User]:
        """Get user by Telegram user ID.
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            User or None if not found
        """
        result = await self.session.execute(
            select(User).where(User.telegram_user_id == telegram_user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_user(
        self,
        telegram_user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None
    ) -> User:
        """Create new user.
        
        Args:
            telegram_user_id: Telegram user ID
            username: Username
            first_name: First name
            last_name: Last name
            phone: Phone number
            
        Returns:
            Created user
        """
        return await self.create(
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone=phone
        )
