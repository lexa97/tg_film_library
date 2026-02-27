"""Film search and confirmation handlers."""

import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_group import UserGroupService
from app.services.film import FilmService
from app.services.group_film import GroupFilmService
from app.services.notification import NotificationService
from app.services.tmdb import TMDBFilmSearch
from app.services.prowlarr import ProwlarrService
from app.services.dto import FilmCreate
from app.keyboards.inline import (
    build_film_confirm_keyboard,
    build_torrent_list_keyboard,
    get_download_search_from_cache,
)
from app.config import get_settings


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
        poster_url=film_details.poster_url,
        duration=film_details.duration,
        director=film_details.director,
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


# Storage for torrent search results (temporary, per callback)
# Format: {message_id: [TorrentResult, ...]}
_torrent_cache: dict[int, list] = {}


@router.callback_query(F.data.startswith("download_search:"))
async def callback_download_search(callback: CallbackQuery, session: AsyncSession):
    """Search for torrents via Prowlarr.
    
    Args:
        callback: Callback query
        session: Database session
    """
    # Parse callback data: download_search:id (cached) or download_search:title:year (legacy)
    cached = get_download_search_from_cache(callback.data)
    if cached:
        title, year = cached
    else:
        parts = callback.data.split(":", 2)
        if len(parts) != 3:
            await callback.answer("❌ Ошибка данных", show_alert=True)
            return
        title = parts[1]
        year_str = parts[2]
        year = int(year_str) if year_str and year_str != "0" else None
    
    await callback.answer("🔍 Ищу раздачи...")
    
    # Initialize Prowlarr service
    settings = get_settings()
    prowlarr = ProwlarrService(
        base_url=settings.prowlarr_url,
        api_key=settings.prowlarr_api_key
    )
    
    # Search torrents
    torrents = await prowlarr.search_torrents(title, year, limit=10)
    
    if not torrents:
        await callback.answer(
            "😕 Раздачи не найдены.\n"
            "Попробуйте другой фильм или проверьте настройки Prowlarr.",
            show_alert=True
        )
        return
    
    # Build message with detailed list
    text = f"📥 <b>Найдено раздач:</b> {len(torrents)}\n\n"
    text += f"<b>{title}</b>"
    if year:
        text += f" ({year})"
    text += "\n\n"
    
    # Add detailed list
    for idx, torrent in enumerate(torrents, 1):
        text += f"<b>{idx}.</b> "
        
        # Resolution (if available)
        if torrent.resolution:
            text += f"{torrent.resolution} · "
        
        # Size and seeders
        text += f"{torrent.size_gb} GB · 👥 {torrent.seeders}\n"
        
        # Full title from Prowlarr (may contain codec, audio, language, etc.)
        text += f"   {torrent.title}\n"
        
        # Source with link to tracker page
        if torrent.info_url:
            text += f"   <a href=\"{torrent.info_url}\">{torrent.indexer}</a>\n\n"
        else:
            text += f"   <i>{torrent.indexer}</i>\n\n"
    
    text += "Нажмите на номер раздачи для скачивания:"
    
    keyboard = build_torrent_list_keyboard(torrents)
    
    sent_message = await callback.message.answer(
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )

    # Cache torrents for exact list message with inline buttons
    _torrent_cache[sent_message.message_id] = torrents


@router.callback_query(F.data.startswith("download_release:"))
async def callback_download_release(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot
):
    """Download release to torrent client via Prowlarr or send torrent file.
    
    Args:
        callback: Callback query
        session: Database session
        bot: Bot instance
    """
    # Parse callback data: download_release:index
    parts = callback.data.split(":")
    if len(parts) != 2:
        await callback.answer("❌ Ошибка данных", show_alert=True)
        return
    
    idx = int(parts[1])
    
    # Get torrent from cache
    message_id = callback.message.message_id
    
    torrents = _torrent_cache.get(message_id)

    # Backward-compatible fallback for older cached entries
    if torrents is None:
        for cached_msg_id, cached_torrents in _torrent_cache.items():
            if abs(cached_msg_id - message_id) < 100:
                torrents = cached_torrents
                break
    
    if not torrents or idx >= len(torrents):
        await callback.answer("❌ Раздача не найдена в кэше", show_alert=True)
        return
    
    torrent = torrents[idx]
    
    # Get user and their group
    user = callback.from_user
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
    
    group_id = membership.group.id
    logger.info(f"Download request from group_id={group_id}, user_id={user.id}")
    
    # Initialize Prowlarr service
    settings = get_settings()
    prowlarr = ProwlarrService(
        base_url=settings.prowlarr_url,
        api_key=settings.prowlarr_api_key
    )
    
    # Check if this group can auto-download via Prowlarr
    if settings.download_group_id and group_id == settings.download_group_id:
        # Auto-download mode: push to download client
        logger.info(f"Auto-download mode for group {group_id}")
        await callback.answer("📥 Отправляю в торрент-клиент...")
        
        success = await prowlarr.push_to_download_client(
            guid=torrent.guid,
            indexer_id=torrent.indexer_id,
            search_query=torrent.search_query,
            info_url=torrent.info_url,
            title=torrent.title,
        )
        
        if success:
            # Send success message
            text = (
                f"✅ <b>Раздача отправлена на скачивание!</b>\n\n"
                f"<b>Название:</b> {torrent.title[:100]}...\n"
                f"<b>Источник:</b> {torrent.indexer}\n"
                f"<b>Размер:</b> {torrent.size_gb} GB\n"
                f"<b>Сиды:</b> {torrent.seeders}\n\n"
                f"<i>Проверьте ваш торрент-клиент для отслеживания прогресса.</i>"
            )
            await callback.message.answer(text=text, parse_mode="HTML")
        else:
            # Send error message
                await callback.message.answer(
                    "❌ <b>Ошибка при отправке раздачи</b>\n\n"
                    "Проверьте:\n"
                    "• Настроен ли торрент-клиент в Prowlarr\n"
                    "• Доступен ли Prowlarr\n"
                    "• Логи бота для деталей",
                    parse_mode="HTML",
                )
    else:
        # Manual download mode: send torrent file or magnet link
        logger.info(f"Manual download mode for group {group_id}")
        await callback.answer("📥 Получаю ссылку...")
        
        torrent_data, magnet_url = await prowlarr.download_torrent_file(torrent.magnet_url)
        
        if torrent_data:
            # Send torrent file
            # Prepare filename (sanitize torrent title)
            filename = f"{torrent.title[:100]}.torrent"
            # Remove illegal characters
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-', '[', ']'))
            
            # Create input file
            input_file = BufferedInputFile(
                file=torrent_data,
                filename=filename
            )
            
            # Send torrent file
            caption = (
                f"📦 <b>{torrent.title[:200]}</b>\n\n"
                f"<b>Источник:</b> {torrent.indexer}\n"
                f"<b>Размер:</b> {torrent.size_gb} GB\n"
                f"<b>Сиды:</b> {torrent.seeders}"
            )
            
            await bot.send_document(
                chat_id=callback.message.chat.id,
                document=input_file,
                caption=caption,
                parse_mode="HTML"
            )
        elif magnet_url:
            # Send magnet link as text
            text = (
                f"🧲 <b>Magnet-ссылка</b>\n\n"
                f"<b>{torrent.title[:200]}</b>\n\n"
                f"<b>Источник:</b> {torrent.indexer}\n"
                f"<b>Размер:</b> {torrent.size_gb} GB\n"
                f"<b>Сиды:</b> {torrent.seeders}\n\n"
                f"<code>{magnet_url}</code>\n\n"
                f"<i>Скопируйте ссылку и добавьте в свой торрент-клиент</i>"
            )
            
            await callback.message.answer(text=text, parse_mode="HTML")
        else:
            # Send error message
            await callback.message.answer(
                "❌ <b>Ошибка при получении раздачи</b>\n\n"
                "Проверьте:\n"
                "• Доступен ли Prowlarr\n"
                "• Логи бота для деталей",
                parse_mode="HTML",
            )
