from aiogram import F, Router
from aiogram.filters.magic import MagicData
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.tmdb import search_multi, result_to_film_data, format_poster_url
from app.services.user_group import get_user_group, get_group_member_telegram_ids, get_or_create_user
from app.services.film import find_film_by_external, create_film, add_film_to_group
from app.keyboards.inline import btn_confirm_film

router = Router()

PAGE_SIZE = 5


@router.message(F.text, ~F.text.startswith("/"))
async def on_text_search(message: Message, session: AsyncSession = MagicData()) -> None:
    query = (message.text or "").strip()
    if not query or len(query) < 2:
        return
    group = await get_user_group(session, message.from_user.id)
    if not group:
        return

    await message.bot.send_chat_action(message.chat.id, "typing")
    results = await search_multi(query, language="ru-RU")
    if not results:
        await message.answer("Ничего не найдено. Попробуйте другое название.")
        return

    for item in results[:PAGE_SIZE]:
        data = result_to_film_data(item)
        title = data["title"]
        year = f" ({data['year']})" if data.get("year") else ""
        desc = (data.get("description") or "")[:400]
        text = f"<b>{title}</b>{year}\n\n{desc}"
        poster = data.get("poster_url")
        kb = btn_confirm_film(data["external_id"], data["source"])
        if poster:
            try:
                await message.answer_photo(poster, caption=text, reply_markup=kb)
            except Exception:
                await message.answer(text, reply_markup=kb)
        else:
            await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("confirm:"))
async def on_confirm_film(callback: CallbackQuery, session: AsyncSession = MagicData()) -> None:
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await callback.answer("Ошибка")
        return
    source, external_id = parts[1], parts[2]
    group = await get_user_group(session, callback.from_user.id)
    if not group:
        await callback.answer("Вы не в группе.")
        return

    from app.services.tmdb import fetch_movie_or_tv

    film_data = await fetch_movie_or_tv(external_id, source)
    if not film_data:
        await callback.answer("Не удалось загрузить данные фильма.")
        return

    film = await find_film_by_external(session, external_id, source)
    if not film:
        film = await create_film(session, film_data)

    user = await get_or_create_user(
        session,
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name,
        callback.from_user.last_name,
    )
    from app.services.user_group import get_or_create_user
    gf = await add_film_to_group(session, group.id, film.id, user.id)
    await callback.answer("Фильм добавлен в список.")

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"«{film.title}» добавлен в список группы «{group.name}».")

    member_ids = await get_group_member_telegram_ids(session, group.id)
    for uid in member_ids:
        if uid == callback.from_user.id:
            continue
        try:
            await callback.bot.send_message(
                uid,
                f"В список группы «{group.name}» добавлен фильм: {film.title}"
                + (f" ({film.year})" if film.year else "") + "."
            )
        except Exception:
            pass
