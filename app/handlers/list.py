"""Film list and watched status handlers."""

import logging
import math
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_group import UserGroupService
from app.services.film import FilmService
from app.services.group_film import GroupFilmService
from app.services.notification import NotificationService
from app.services.tmdb import TMDBFilmSearch
from app.keyboards.inline import build_film_list_keyboard, build_film_detail_keyboard
from app.config import get_settings


logger = logging.getLogger(__name__)
router = Router()
settings = get_settings()


async def show_film_list(
    message: Message,
    session: AsyncSession,
    page: int = 0,
    edit: bool = False
):
    """Show film list for user's group.
    
    Args:
        message: Telegram message
        session: Database session
        page: Page number (0-indexed)
        edit: Whether to edit message instead of sending new
    """
    user = message.from_user
    
    # Get user and group
    user_service = UserGroupService(session)
    db_user = await user_service.get_or_create_user(
        telegram_user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    membership = await user_service.get_user_group(db_user.id)
    if not membership:
        text = "❌ Вы не состоите ни в одной группе."
        if edit:
            await message.edit_text(text)
        else:
            await message.answer(text)
        return
    
    group = membership.group
    
    # Get films
    search_provider = TMDBFilmSearch()
    film_service = FilmService(session, search_provider)
    group_film_service = GroupFilmService(session, film_service)
    
    films, total = await group_film_service.get_group_films(
        group_id=group.id,
        limit=settings.films_per_page,
        offset=page * settings.films_per_page
    )
    
    if total == 0:
        text = (
            f"📋 <b>Список группы «{group.name}»</b>\n\n"
            f"Список пуст. Начните добавлять фильмы, отправив боту название!"
        )
        if edit:
            await message.edit_text(text, parse_mode="HTML")
        else:
            await message.answer(text, parse_mode="HTML")
        return
    
    total_pages = math.ceil(total / settings.films_per_page)
    
    text = (
        f"📋 <b>Список группы «{group.name}»</b>\n\n"
        f"Всего фильмов: {total}\n"
        f"Выберите фильм для просмотра деталей:"
    )
    
    keyboard = build_film_list_keyboard(films, page, total_pages)
    
    if edit:
        await message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data == "list")
async def callback_list(callback: CallbackQuery, session: AsyncSession):
    """Handle list callback.
    
    Args:
        callback: Callback query
        session: Database session
    """
    await show_film_list(callback.message, session, page=0, edit=True)
    await callback.answer()


@router.callback_query(F.data.startswith("list_page:"))
async def callback_list_page(callback: CallbackQuery, session: AsyncSession):
    """Handle pagination callback.
    
    Args:
        callback: Callback query
        session: Database session
    """
    page = int(callback.data.split(":")[1])
    await show_film_list(callback.message, session, page=page, edit=True)
    await callback.answer()


@router.callback_query(F.data.startswith("film_detail:"))
async def callback_film_detail(callback: CallbackQuery, session: AsyncSession):
    """Show film details.
    
    Args:
        callback: Callback query
        session: Database session
    """
    group_film_id = int(callback.data.split(":")[1])
    
    # Get film
    search_provider = TMDBFilmSearch()
    film_service = FilmService(session, search_provider)
    group_film_service = GroupFilmService(session, film_service)
    
    group_film = await group_film_service.get_group_film_by_id(group_film_id)
    if not group_film:
        await callback.answer("❌ Фильм не найден", show_alert=True)
        return
    
    film = group_film.film
    is_watched = group_film.watched is not None
    
    # Build text
    text = f"<b>{film.title}</b>"
    if film.year:
        text += f" ({film.year})"
    
    if film.title_original and film.title_original != film.title:
        text += f"\n<i>{film.title_original}</i>"
    
    if film.description:
        text += f"\n\n{film.description}"
    
    if is_watched:
        text += "\n\n✅ <b>Просмотрено</b>"
    
    keyboard = build_film_detail_keyboard(group_film_id, is_watched)
    
    # Send with poster if available
    if film.poster_url:
        try:
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=film.poster_url,
                caption=text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            await callback.message.edit_text(
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
    else:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("mark_watched:"))
async def callback_mark_watched(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Mark film as watched.
    
    Args:
        callback: Callback query
        session: Database session
        bot: Bot instance
    """
    group_film_id = int(callback.data.split(":")[1])
    user = callback.from_user
    
    # Get user
    user_service = UserGroupService(session)
    db_user = await user_service.get_or_create_user(
        telegram_user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    membership = await user_service.get_user_group(db_user.id)
    if not membership:
        await callback.answer("❌ Вы не состоите ни в одной группе", show_alert=True)
        return
    
    group = membership.group
    
    # Mark as watched
    search_provider = TMDBFilmSearch()
    film_service = FilmService(session, search_provider)
    group_film_service = GroupFilmService(session, film_service)
    
    try:
        await group_film_service.mark_watched(
            group_film_id=group_film_id,
            marked_by_user_id=db_user.id
        )
        
        # Get updated group film
        group_film = await group_film_service.get_group_film_by_id(group_film_id)
        film = group_film.film
        
        # Update keyboard
        keyboard = build_film_detail_keyboard(group_film_id, is_watched=True)
        
        # Update message
        text = callback.message.caption if callback.message.caption else callback.message.text
        if not text.endswith("✅ <b>Просмотрено</b>"):
            text += "\n\n✅ <b>Просмотрено</b>"
        
        try:
            if callback.message.photo:
                await callback.message.edit_caption(
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            else:
                await callback.message.edit_text(
                    text=text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
        except Exception as e:
            logger.error(f"Error updating message: {e}")
        
        await callback.answer("✅ Фильм отмечен как просмотренный!")
        
        # Notify group members
        members = await user_service.get_group_members(group.id)
        members_to_notify = [m for m in members if m.telegram_user_id != user.id]
        
        if members_to_notify:
            notification_service = NotificationService(bot)
            await notification_service.notify_film_watched(
                users=members_to_notify,
                film=film,
                marked_by_name=user.first_name or user.username or "Участник",
                group_name=group.name,
                admin_telegram_id=group.admin.telegram_user_id
            )
        
    except ValueError as e:
        await callback.answer(f"❌ {str(e)}", show_alert=True)
    except Exception as e:
        logger.error(f"Error marking as watched: {e}")
        await callback.answer("❌ Ошибка при отметке фильма", show_alert=True)


@router.callback_query(F.data == "noop")
async def callback_noop(callback: CallbackQuery):
    """Handle no-op callback (pagination info).
    
    Args:
        callback: Callback query
    """
    await callback.answer()
