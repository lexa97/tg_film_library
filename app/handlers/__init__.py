from aiogram import Router

from app.handlers import start, group, film_search, list_watched

router = Router()
router.include_router(start.router)
router.include_router(group.router)
router.include_router(film_search.router)
router.include_router(list_watched.router)

__all__ = ["router"]
