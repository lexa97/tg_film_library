"""Basic command handlers."""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_group import UserGroupService
from app.keyboards.inline import build_main_menu_keyboard


logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession):
    """Handle /start command.
    
    Args:
        message: Telegram message
        session: Database session
    """
    user = message.from_user
    
    # Get or create user
    service = UserGroupService(session)
    db_user = await service.get_or_create_user(
        telegram_user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Check if user is in a group
    membership = await service.get_user_group(db_user.id)
    
    if membership:
        # User is in a group
        group = membership.group
        text = (
            f"👋 Привет, {user.first_name}!\n\n"
            f"Вы участник группы: <b>{group.name}</b>\n\n"
            f"Отправьте название фильма для поиска или используйте кнопки ниже."
        )
        keyboard = build_main_menu_keyboard(has_group=True)
    else:
        # User is not in any group
        text = (
            f"👋 Привет, {user.first_name}!\n\n"
            f"Вас ещё нет ни в одной группе.\n\n"
            f"Вы можете:\n"
            f"• Создать свою группу с помощью кнопки ниже\n"
            f"• Попросить администратора группы добавить вас, отправив ему ваш контакт "
            f"(Настройки → Поделиться контактом)"
        )
        keyboard = build_main_menu_keyboard(has_group=False)
    
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.message(Command("list"))
async def cmd_list(message: Message, session: AsyncSession):
    """Handle /list command.
    
    Args:
        message: Telegram message
        session: Database session
    """
    from app.handlers.list import show_film_list
    await show_film_list(message, session, page=0)
