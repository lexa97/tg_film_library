"""Context var для доступа к data (session, сервисы) внутри хендлеров.

Aiogram вызывает хендлер только с (event); middleware кладёт data сюда,
и хендлеры читают его через get_handler_data().
"""
import contextvars
from typing import Any

HANDLER_DATA: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "handler_data", default=None
)


def get_handler_data() -> dict[str, Any]:
    """Вернуть data для текущего апдейта. Вызывать в хендлерах."""
    data = HANDLER_DATA.get()
    if data is None:
        raise RuntimeError("handler_data not set (middleware order?)")
    return data
