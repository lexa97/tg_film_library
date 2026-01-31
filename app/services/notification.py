"""Notification service."""

import logging
from typing import Optional
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from app.db.models import User, Film


logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications to users."""
    
    def __init__(self, bot: Bot):
        """Initialize service.
        
        Args:
            bot: Telegram bot instance
        """
        self.bot = bot
    
    async def notify_film_added(
        self,
        users: list[User],
        film: Film,
        added_by_name: str,
        group_name: str,
        admin_telegram_id: Optional[int] = None
    ) -> None:
        """Notify users about new film added to group.
        
        Args:
            users: List of users to notify
            film: Added film
            added_by_name: Name of user who added the film
            group_name: Group name
            admin_telegram_id: Admin's Telegram ID (for error reports)
        """
        message = (
            f"📽 Новый фильм в группе «{group_name}»\n\n"
            f"<b>{film.title}</b>"
        )
        if film.year:
            message += f" ({film.year})"
        
        message += f"\n\nДобавил: {added_by_name}"
        
        for user in users:
            try:
                await self.bot.send_message(
                    chat_id=user.telegram_user_id,
                    text=message,
                    parse_mode="HTML"
                )
            except TelegramForbiddenError:
                logger.warning(f"User {user.telegram_user_id} has blocked the bot")
                # Notify admin if available
                if admin_telegram_id:
                    try:
                        await self.bot.send_message(
                            chat_id=admin_telegram_id,
                            text=f"⚠️ Пользователь {user.first_name or user.username or 'Unknown'} заблокировал бота и не получит уведомления."
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify admin: {e}")
            except TelegramBadRequest as e:
                logger.error(f"Failed to send notification to {user.telegram_user_id}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error sending notification: {e}")
    
    async def notify_film_watched(
        self,
        users: list[User],
        film: Film,
        marked_by_name: str,
        group_name: str,
        admin_telegram_id: Optional[int] = None
    ) -> None:
        """Notify users about film marked as watched.
        
        Args:
            users: List of users to notify
            film: Watched film
            marked_by_name: Name of user who marked as watched
            group_name: Group name
            admin_telegram_id: Admin's Telegram ID (for error reports)
        """
        message = (
            f"✅ Фильм просмотрен в группе «{group_name}»\n\n"
            f"<b>{film.title}</b>"
        )
        if film.year:
            message += f" ({film.year})"
        
        message += f"\n\nОтметил: {marked_by_name}"
        
        for user in users:
            try:
                await self.bot.send_message(
                    chat_id=user.telegram_user_id,
                    text=message,
                    parse_mode="HTML"
                )
            except TelegramForbiddenError:
                logger.warning(f"User {user.telegram_user_id} has blocked the bot")
                if admin_telegram_id:
                    try:
                        await self.bot.send_message(
                            chat_id=admin_telegram_id,
                            text=f"⚠️ Пользователь {user.first_name or user.username or 'Unknown'} заблокировал бота и не получит уведомления."
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify admin: {e}")
            except TelegramBadRequest as e:
                logger.error(f"Failed to send notification to {user.telegram_user_id}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error sending notification: {e}")
    
    async def notify_member_added(
        self,
        user: User,
        group_name: str,
        admin_name: str
    ) -> None:
        """Notify user that they were added to a group.
        
        Args:
            user: User who was added
            group_name: Group name
            admin_name: Admin's name
        """
        message = (
            f"👥 Вы добавлены в группу\n\n"
            f"Группа: <b>{group_name}</b>\n"
            f"Добавил: {admin_name}\n\n"
            f"Теперь вы можете искать фильмы и добавлять их в общий список!"
        )
        
        try:
            await self.bot.send_message(
                chat_id=user.telegram_user_id,
                text=message,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to notify user about being added: {e}")
