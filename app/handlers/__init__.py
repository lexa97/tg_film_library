from aiogram import Router

from app.handlers import start, group, film_search, list_watched

router = Router(name="root")
router.include_router(start.router, name="start")
router.include_router(group.router, name="group")
router.include_router(film_search.router, name="film_search")
router.include_router(list_watched.router, name="list_watched")

__all__ = ["router"]
