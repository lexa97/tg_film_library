"""Отправка карточек результатов поиска (общий вид с film.py)."""

import logging

from aiogram.types import Message

from app.keyboards.inline import build_film_confirm_keyboard
from app.services.dto import FilmSearchResult

logger = logging.getLogger(__name__)


async def send_film_search_result_cards(
    message: Message,
    results: list[FilmSearchResult],
    intro_line: str,
) -> None:
    """Текст + постер + клавиатура «Подтвердить» / «Скачать» для каждого результата."""
    if not results:
        return
    await message.answer(intro_line)
    for i, result in enumerate(results):
        text = f"<b>{result.title}</b>"
        if result.year:
            text += f" ({result.year})"
        if result.title_original and result.title_original != result.title:
            text += f"\n<i>{result.title_original}</i>"
        if result.description:
            desc = (
                result.description[:300] + "..."
                if len(result.description) > 300
                else result.description
            )
            text += f"\n\n{desc}"
        media_type_text = "Фильм" if result.media_type == "movie" else "Сериал"
        text += f"\n\n📺 {media_type_text}"
        keyboard = build_film_confirm_keyboard(result, i)
        if result.poster_url:
            try:
                await message.answer_photo(
                    photo=result.poster_url,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
            except Exception as e:
                logger.error("Error sending photo: %s", e)
                await message.answer(
                    text=text,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
        else:
            await message.answer(
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
