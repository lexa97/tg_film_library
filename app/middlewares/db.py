"""Database session middleware."""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.db.database import async_session_maker


class DatabaseMiddleware(BaseMiddleware):
    """Middleware to provide database session to handlers."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process update with database session.
        
        Args:
            handler: Handler function
            event: Telegram event
            data: Handler data
            
        Returns:
            Handler result
        """
        async with async_session_maker() as session:
            data["session"] = session
            return await handler(event, data)
