"""Film search and confirmation handlers."""

import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_group import UserGroupService
from app.services.film import FilmService
from app.services.group_film import GroupFilmService
from app.services.notification import NotificationService
from app.services.tmdb import TMDBFilmSearch
from app.services.dto import FilmCreate
from app.keyboards.inline import build_film_confirm_keyboard


logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text & ~F.text.startswith("/"))
async def search_film(message: Message, session: AsyncSession):
    """Handle text message as film search query.
    
    Args:
        message: Telegram message
        session: Database session
    """
    user = message.from_user
    query = message.text.strip()
    
    # Check if user is in a group
    user_service = UserGroupService(session)
    db_user = await user_service.get_or_create_user(
        telegram_user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    membership = await user_service.get_user_group(db_user.id)
    if not membership:
        await message.answer(
            "❌ Вы не состоите ни в одной группе.\n"
            "Создайте группу или попросите администратора добавить вас."
        )
        return
    
    # Search films
    search_provider = TMDBFilmSearch()
    film_service = FilmService(session, search_provider)
    
    results = await film_service.search_films(query, language="ru")
    
    # Check for API error
    if results is None:
        await message.answer(
            "❌ Не удалось выполнить поиск. Возможно, проблемы с подключением к базе данных фильмов.\n"
            "Попробуйте позже."
        )
        return
    
    # Check for empty results
    if not results:
        await message.answer(
            f"😕 По запросу «{query}» ничего не найдено.\n"
            "Попробуйте другое название."
        )
        return
    
    # Send results
    await message.answer(f"🔍 Найдено результатов: {len(results)}\n")
    
    for i, result in enumerate(results):
        text = f"<b>{result.title}</b>"
        if result.year:
            text += f" ({result.year})"
        
        if result.title_original and result.title_original != result.title:
            text += f"\n<i>{result.title_original}</i>"
        
        if result.description:
            # Truncate long descriptions
            desc = result.description[:300] + "..." if len(result.description) > 300 else result.description
            text += f"\n\n{desc}"
        
        media_type_text = "Фильм" if result.media_type == "movie" else "Сериал"
        text += f"\n\n📺 {media_type_text}"
        
        keyboard = build_film_confirm_keyboard(result, i)
        
        # Send with poster if available
        if result.poster_url:
            try:
                await message.answer_photo(
                    photo=result.poster_url,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Error sending photo: {e}")
                await message.answer(
                    text=text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
        else:
            await message.answer(
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard
            )


@router.callback_query(F.data.startswith("confirm_film:"))
async def confirm_film(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Handle film confirmation.
    
    Args:
        callback: Callback query
        session: Database session
        bot: Bot instance
    """
    # Parse callback data: confirm_film:external_id:media_type:index
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer("❌ Ошибка данных", show_alert=True)
        return
    
    external_id = parts[1]
    media_type = parts[2]
    
    user = callback.from_user
    
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
        await callback.answer("❌ Вы не состоите ни в одной группе", show_alert=True)
        return
    
    group = membership.group
    
    # Get film details
    search_provider = TMDBFilmSearch()
    film_service = FilmService(session, search_provider)
    
    film_details = await film_service.get_film_details(external_id, media_type)
    if not film_details:
        await callback.answer("❌ Не удалось загрузить данные фильма", show_alert=True)
        return
    
    # Add film to group
    group_film_service = GroupFilmService(session, film_service)
    
    film_data = FilmCreate(
        external_id=film_details.external_id,
        source=film_details.source,
        title=film_details.title,
        title_original=film_details.title_original,
        year=film_details.year,
        description=film_details.description,
        poster_url=film_details.poster_url
    )
    
    try:
        group_film = await group_film_service.add_film_to_group(
            group_id=group.id,
            film_data=film_data,
            added_by_user_id=db_user.id
        )
        
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.answer("✅ Фильм добавлен в список группы!")
        
        # Notify group members
        members = await user_service.get_group_members(group.id)
        # Exclude the user who added
        members_to_notify = [m for m in members if m.telegram_user_id != user.id]
        
        if members_to_notify:
            notification_service = NotificationService(bot)
            await notification_service.notify_film_added(
                users=members_to_notify,
                film=group_film.film,
                added_by_name=user.first_name or user.username or "Участник",
                group_name=group.name,
                admin_telegram_id=group.admin.telegram_user_id
            )
        
    except ValueError as e:
        await callback.answer(f"❌ {str(e)}", show_alert=True)
    except Exception as e:
        logger.error(f"Error adding film to group: {e}")
        await callback.answer("❌ Ошибка при добавлении фильма", show_alert=True)
