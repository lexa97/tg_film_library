"""Inline keyboards for bot."""

from typing import Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db.models import GroupFilm
from app.services.dto import FilmSearchResult, TorrentResult


def build_main_menu_keyboard(has_group: bool) -> InlineKeyboardMarkup:
    """Build main menu keyboard.
    
    Args:
        has_group: Whether user is in a group
        
    Returns:
        Inline keyboard
    """
    builder = InlineKeyboardBuilder()
    
    if has_group:
        builder.row(
            InlineKeyboardButton(text="📋 Мой список", callback_data="list")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="➕ Создать группу", callback_data="create_group")
        )
    
    return builder.as_markup()


def build_film_confirm_keyboard(
    result: FilmSearchResult,
    index: int
) -> InlineKeyboardMarkup:
    """Build keyboard for film search result confirmation.
    
    Args:
        result: Film search result
        index: Result index for callback data
        
    Returns:
        Inline keyboard with Confirm and Magnet buttons
    """
    builder = InlineKeyboardBuilder()
    
    callback_data = f"confirm_film:{result.external_id}:{result.media_type}:{index}"
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=callback_data)
    )
    
    # Add download button
    download_data = f"download_search:{result.title}:{result.year or 0}"
    builder.row(
        InlineKeyboardButton(text="📥 Скачать", callback_data=download_data)
    )
    
    return builder.as_markup()


def build_film_list_keyboard(
    films: list[GroupFilm],
    page: int = 0,
    total_pages: int = 1
) -> InlineKeyboardMarkup:
    """Build keyboard with film list.
    
    Args:
        films: List of group films
        page: Current page (0-indexed)
        total_pages: Total number of pages
        
    Returns:
        Inline keyboard with film names as buttons
    """
    builder = InlineKeyboardBuilder()
    
    # Film buttons
    for group_film in films:
        film = group_film.film
        watched_prefix = "✓ " if group_film.watched else ""
        button_text = f"{watched_prefix}{film.title}"
        if film.year:
            button_text += f" ({film.year})"
        
        # Truncate long titles
        if len(button_text) > 60:
            button_text = button_text[:57] + "..."
        
        builder.row(
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"film_detail:{group_film.id}"
            )
        )
    
    # Pagination buttons
    if total_pages > 1:
        pagination_buttons = []
        
        if page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(text="◀️ Назад", callback_data=f"list_page:{page-1}")
            )
        
        pagination_buttons.append(
            InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop")
        )
        
        if page < total_pages - 1:
            pagination_buttons.append(
                InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"list_page:{page+1}")
            )
        
        builder.row(*pagination_buttons)
    
    return builder.as_markup()


def build_film_detail_keyboard(
    group_film_id: int,
    is_watched: bool,
    film_title: str,
    film_year: Optional[int] = None
) -> InlineKeyboardMarkup:
    """Build keyboard for film detail view.
    
    Args:
        group_film_id: Group film ID
        is_watched: Whether film is already watched
        film_title: Film title for magnet search
        film_year: Film year for magnet search
        
    Returns:
        Inline keyboard with Watched and Magnet buttons
    """
    builder = InlineKeyboardBuilder()
    
    if not is_watched:
        builder.row(
            InlineKeyboardButton(
                text="✅ Просмотрено",
                callback_data=f"mark_watched:{group_film_id}"
            )
        )
    
    # Add download button
    download_data = f"download_search:{film_title}:{film_year or 0}"
    builder.row(
        InlineKeyboardButton(text="📥 Скачать", callback_data=download_data)
    )
    
    builder.row(
        InlineKeyboardButton(text="◀️ К списку", callback_data="list")
    )
    
    return builder.as_markup()


def build_torrent_list_keyboard(
    torrents: list[TorrentResult]
) -> InlineKeyboardMarkup:
    """Build keyboard with torrent list.
    
    Args:
        torrents: List of torrent results
        
    Returns:
        Inline keyboard with numbered buttons (3-5 per row)
    """
    builder = InlineKeyboardBuilder()
    
    # Create numbered buttons
    buttons = []
    for idx in range(len(torrents)):
        buttons.append(
            InlineKeyboardButton(
                text=f"#{idx + 1}",
                callback_data=f"download_release:{idx}"
            )
        )
    
    # Add buttons in rows (5 buttons per row max)
    for i in range(0, len(buttons), 5):
        row_buttons = buttons[i:i+5]
        builder.row(*row_buttons)
    
    return builder.as_markup()
