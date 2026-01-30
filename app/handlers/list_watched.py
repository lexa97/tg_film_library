from aiogram import F, Router
from aiogram.filters import Command
from aiogram.filters.magic import MagicData
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_group import get_user_group, get_group_member_telegram_ids, get_or_create_user
from app.services.film import get_group_films, get_group_film_by_id, mark_as_watched, is_watched
from app.keyboards.inline import list_film_buttons, btn_watched

router = Router()

PAGE_SIZE = 10


@router.message(Command("list"))
async def cmd_list(message: Message, session: AsyncSession = MagicData()) -> None:
    await _send_list(message.chat.id, message.bot, session, message.from_user.id, page=0)


@router.callback_query(F.data == "mylist")
async def cb_mylist(callback: CallbackQuery, session: AsyncSession = MagicData()) -> None:
    await callback.answer()
    await _send_list(callback.message.chat.id, callback.bot, session, callback.from_user.id, page=0)
    try:
        await callback.message.delete()
    except Exception:
        pass


@router.callback_query(F.data.startswith("page:"))
async def cb_page(callback: CallbackQuery, session: AsyncSession = MagicData()) -> None:
    try:
        page = int(callback.data.split(":", 1)[1])
    except (IndexError, ValueError):
        page = 0
    await callback.answer()
    await _send_list(callback.message.chat.id, callback.bot, session, callback.from_user.id, page=page)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.delete()
    except Exception:
        pass


async def _send_list(chat_id: int, bot, session: AsyncSession, telegram_user_id: int, page: int = 0) -> None:
    group = await get_user_group(session, telegram_user_id)
    if not group:
        await bot.send_message(chat_id, "Вы не в группе. Сначала попросите админа добавить вас.")
        return

    offset = page * PAGE_SIZE
    rows = await get_group_films(session, group.id, limit=PAGE_SIZE + 1, offset=offset)
    has_next = len(rows) > PAGE_SIZE
    if has_next:
        rows = rows[:PAGE_SIZE]
    items = [(gf.id, f.title, watched) for gf, f, watched in rows]

    if not items:
        await bot.send_message(chat_id, "В списке пока ничего нет. Отправьте название фильма, чтобы добавить.")
        return

    kb = list_film_buttons(items, page=page, has_next=has_next)
    await bot.send_message(
        chat_id,
        f"Список группы «{group.name}» (✓ — просмотрено):",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("gf:"))
async def cb_film_detail(callback: CallbackQuery, session: AsyncSession) -> None:
    try:
        gf_id = int(callback.data.split(":", 1)[1])
    except (IndexError, ValueError):
        await callback.answer("Ошибка")
        return
    group = await get_user_group(session, callback.from_user.id)
    if not group:
        await callback.answer("Вы не в группе.")
        return

    row = await get_group_film_by_id(session, gf_id, group.id)
    if not row:
        await callback.answer("Фильм не найден.")
        return
    gf, film = row
    watched = await is_watched(session, gf.id)
    text = f"<b>{film.title}</b>"
    if film.year:
        text += f" ({film.year})"
    text += "\n\n" + (film.description or "Нет описания.")
    if watched:
        text += "\n\n✓ Просмотрено."
    kb = None if watched else btn_watched(gf.id)
    if film.poster_url:
        try:
            await callback.message.answer_photo(
                film.poster_url,
                caption=text,
                reply_markup=kb,
            )
        except Exception:
            await callback.message.answer(text, reply_markup=kb)
    else:
        await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("watched:"))
async def cb_watched(callback: CallbackQuery, session: AsyncSession = MagicData()) -> None:
    try:
        gf_id = int(callback.data.split(":", 1)[1])
    except (IndexError, ValueError):
        await callback.answer("Ошибка")
        return
    group = await get_user_group(session, callback.from_user.id)
    if not group:
        await callback.answer("Вы не в группе.")
        return

    row = await get_group_film_by_id(session, gf_id, group.id)
    if not row:
        await callback.answer("Фильм не найден.")
        return
    gf, film = row
    user = await get_or_create_user(
        session,
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name,
        callback.from_user.last_name,
    )
    await mark_as_watched(session, gf.id, user.id)
    await callback.answer("Отмечено как просмотрено.")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer("✓ Отмечено как просмотрено.")
    except Exception:
        await callback.message.answer("✓ Отмечено как просмотрено.")

    member_ids = await get_group_member_telegram_ids(session, group.id)
    for uid in member_ids:
        if uid == callback.from_user.id:
            continue
        try:
            await callback.bot.send_message(
                uid,
                f"В группе «{group.name}» фильм «{film.title}» отмечен как просмотренный."
            )
        except Exception:
            pass
