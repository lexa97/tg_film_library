"""Main bot entry point."""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import get_settings
from app.middlewares.db import DatabaseMiddleware
from app.handlers import commands, group, member, film, list as list_handler


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to start the bot."""
    # Load settings
    settings = get_settings()
    
    # Initialize bot and dispatcher
    bot = Bot(token=settings.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register middlewares
    dp.update.middleware(DatabaseMiddleware())
    
    # Register routers
    dp.include_router(commands.router)
    dp.include_router(group.router)
    dp.include_router(member.router)
    dp.include_router(film.router)
    dp.include_router(list_handler.router)
    
    # Start polling
    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
