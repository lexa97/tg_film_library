"""Middleware: добавляет сервисы в data для хендлеров."""
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.container import get_film_search, get_group_film_service, get_user_group_service


class ServicesMiddleware(BaseMiddleware):
    """Добавляет user_group_service, group_film_service, film_search в data."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["user_group_service"] = get_user_group_service()
        data["group_film_service"] = get_group_film_service()
        data["film_search"] = get_film_search()
        return await handler(event, data)
