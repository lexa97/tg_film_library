"""Main bot entry point."""

import asyncio
import logging
import httpx
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from app.config import get_settings
from app.db.database import async_session_maker
from app.middlewares.db import DatabaseMiddleware
from app.handlers import commands, group, member, film, list as list_handler
from app.services.recommendation_refresh import refresh_recommendation_cache_for_all_sources
from app.services.tmdb import TMDBFilmSearch


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_tmdb_connection():
    """Test TMDB API connection at startup."""
    settings = get_settings()
    headers = {
        "Authorization": f"Bearer {settings.tmdb_api_key}",
        "accept": "application/json"
    }
    
    try:
        logger.info("Testing TMDB API connection...")
        if settings.proxy_url:
            logger.info(f"Using proxy: {settings.proxy_url}")
        
        # Создаем клиент с прокси если указан
        client_kwargs = {"timeout": 10.0}
        if settings.proxy_url:
            client_kwargs["proxy"] = settings.proxy_url
        
        async with httpx.AsyncClient(**client_kwargs) as client:
            response = await client.get(
                "https://api.themoviedb.org/3/configuration",
                headers=headers
            )
            response.raise_for_status()
            logger.info("✅ TMDB API connection successful!")
            return True
    except httpx.ConnectError as e:
        logger.error(f"❌ TMDB connection error (check network/DNS/proxy): {e}")
        return False
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ TMDB auth error {e.response.status_code}: Check your TMDB_API_KEY")
        logger.error(f"Response: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"❌ TMDB test failed: {type(e).__name__}: {e}")
        return False


async def recommendation_cache_background_loop() -> None:
    """Периодически обновляет film_recommendation_cache (не блокирует polling)."""
    settings = get_settings()
    await asyncio.sleep(settings.recommendation_initial_delay_sec)
    search = TMDBFilmSearch()
    interval_sec = max(3600.0, settings.recommendation_cache_interval_hours * 3600)
    while True:
        try:
            async with async_session_maker() as session:
                await refresh_recommendation_cache_for_all_sources(
                    session,
                    search,
                    delay_between_requests_sec=settings.recommendation_tmdb_delay_sec,
                )
                await session.commit()
        except Exception:
            logger.exception("Фоновое обновление кэша рекомендаций завершилось с ошибкой")
        await asyncio.sleep(interval_sec)


async def main():
    """Main function to start the bot."""
    # Load settings
    settings = get_settings()
    
    # Test TMDB connection
    await test_tmdb_connection()
    
    # Initialize bot and dispatcher
    bot = Bot(token=settings.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register middlewares
    dp.update.middleware(DatabaseMiddleware())
    
    # Register routers (order matters! Specific handlers first, generic last)
    dp.include_router(commands.router)
    dp.include_router(list_handler.router)  # Reply-кнопки для списка
    dp.include_router(group.router)  # Reply-кнопка создания группы
    dp.include_router(member.router)
    dp.include_router(film.router)  # Общий обработчик текста - последним!
    
    # Set bot commands menu
    await bot.set_my_commands([
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="list", description="Список фильмов группы"),
        BotCommand(command="relative", description="Похожие на просмотренное"),
    ])

    asyncio.create_task(recommendation_cache_background_loop())

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
