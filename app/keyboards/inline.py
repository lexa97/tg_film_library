# Callback data: до 64 байт. Используем короткие префиксы.
# confirm:film:{external_id}:{source}  -> source=tmdb, external_id до ~50
# list:gf:{group_film_id}
# watched:{group_film_id}
# page:{offset}

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def btn_confirm_film(external_id: str, source: str = "tmdb") -> InlineKeyboardMarkup:
    cb = f"confirm:{source}:{external_id}"[:64]
    return InlineKeyboardBuilder().button(text="Подтвердить", callback_data=cb).as_markup()


def btn_watched(group_film_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardBuilder().button(text="Просмотрено", callback_data=f"watched:{group_film_id}").as_markup()


def list_film_buttons(
    items: list[tuple[int, str, bool]],
    page: int = 0,
    has_next: bool = False,
) -> InlineKeyboardMarkup:
    """items: (group_film_id, title, is_watched). Каждая кнопка — отдельный ряд."""
    builder = InlineKeyboardBuilder()
    for gf_id, title, is_watched in items:
        label = ("✓ " if is_watched else "") + (title[:36] + "…" if len(title) > 36 else title)
        builder.button(text=label, callback_data=f"gf:{gf_id}")
    if page > 0 or has_next:
        row = []
        if page > 0:
            row.append(InlineKeyboardButton(text="← Назад", callback_data=f"page:{page - 1}"))
        if has_next:
            row.append(InlineKeyboardButton(text="Вперёд →", callback_data=f"page:{page + 1}"))
        builder.row(*row)
    return builder.as_markup()


def pagination_buttons(offset: int, has_prev: bool, has_next: bool) -> list[list[InlineKeyboardButton]]:
    row = []
    if has_prev:
        row.append(InlineKeyboardButton(text="← Назад", callback_data=f"page:{offset - 1}"))
    if has_next:
        row.append(InlineKeyboardButton(text="Вперёд →", callback_data=f"page:{offset + 1}"))
    return [row] if row else []


def btn_list() -> InlineKeyboardMarkup:
    return InlineKeyboardBuilder().button(text="Мой список", callback_data="mylist").as_markup()
