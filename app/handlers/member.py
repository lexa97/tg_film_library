"""Member management handlers."""

import logging
from aiogram import Router, F, Bot
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_group import UserGroupService
from app.services.notification import NotificationService


logger = logging.getLogger(__name__)
router = Router()


@router.message(F.content_type == "contact")
async def handle_contact(message: Message, session: AsyncSession, bot: Bot):
    """Handle contact sharing for adding members to group.
    
    Args:
        message: Telegram message with contact
        session: Database session
        bot: Bot instance
    """
    contact = message.contact
    
    if not contact.user_id:
        await message.answer(
            "❌ Не удалось получить Telegram ID из контакта.\n"
            "Убедитесь, что вы отправляете контакт пользователя Telegram "
            "(Поделиться контактом из профиля), а не просто номер из телефонной книги."
        )
        return
    
    user = message.from_user
    service = UserGroupService(session)
    
    # Get admin user
    admin_user = await service.get_or_create_user(
        telegram_user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Add member to group
    try:
        membership, group = await service.add_member_by_contact(
            admin_user_id=admin_user.id,
            contact_telegram_user_id=contact.user_id
        )
        
        added_user = membership.user
        
        # Notify admin
        await message.answer(
            f"✅ Пользователь {added_user.first_name or added_user.username or 'Unknown'} "
            f"добавлен в группу «{group.name}»"
        )
        
        # Notify added user
        notification_service = NotificationService(bot)
        await notification_service.notify_member_added(
            user=added_user,
            group_name=group.name,
            admin_name=user.first_name or user.username or "Администратор"
        )
        
    except ValueError as e:
        await message.answer(f"❌ {str(e)}")
    except Exception as e:
        logger.error(f"Error adding member: {e}")
        await message.answer(
            "❌ Произошла ошибка при добавлении участника. Попробуйте позже."
        )
