"""Reply keyboards for bot."""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def build_main_reply_keyboard(has_group: bool = False) -> ReplyKeyboardMarkup:
    """Build main reply keyboard.
    
    Args:
        has_group: Whether user is in a group
        
    Returns:
        Reply keyboard markup
    """
    builder = ReplyKeyboardBuilder()
    
    if has_group:
        # Кнопки для пользователя в группе
        builder.row(
            KeyboardButton(text="📋 Мой список"),
            KeyboardButton(text="🔍 Найти фильм")
        )
    else:
        # Кнопки для пользователя без группы
        builder.row(
            KeyboardButton(text="➕ Создать группу")
        )
    
    return builder.as_markup(
        resize_keyboard=True,  # Подстраивать размер под кнопки
        persistent=True  # Клавиатура всегда видна
    )


def remove_reply_keyboard() -> ReplyKeyboardMarkup:
    """Remove reply keyboard.
    
    Returns:
        Markup to remove keyboard
    """
    from aiogram.types import ReplyKeyboardRemove
    return ReplyKeyboardRemove()
