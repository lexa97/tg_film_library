"""
Inner middleware: кладёт data в context var и передаёт управление дальше.
Aiogram вызывает хендлер только с (event), поэтому хендлеры читают data через get_handler_data().
"""
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.context import HANDLER_DATA


class InjectDataMiddleware(BaseMiddleware):
    """Устанавливает HANDLER_DATA для текущего апдейта, затем вызывает handler(event, data)."""

    async def __call__(
        self,
        handler: Callable[..., Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        token = HANDLER_DATA.set(data)
        try:
            return await handler(event, data)
        finally:
            HANDLER_DATA.reset(token)
