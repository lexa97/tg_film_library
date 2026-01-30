from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator

import pytest
from aiogram import Bot
from aiogram.types import User as TgUser, Chat, Message as TgMessage, Contact
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_bot() -> Bot:
    """Мок бота Telegram."""
    bot = MagicMock(spec=Bot)
    bot.send_message = AsyncMock()
    bot.send_chat_action = AsyncMock()
    bot.send_photo = AsyncMock()
    return bot


@pytest.fixture
def mock_session() -> AsyncSession:
    """Мок сессии БД."""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def telegram_user() -> TgUser:
    """Тестовый пользователь Telegram."""
    return TgUser(
        id=12345,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="testuser",
    )


@pytest.fixture
def telegram_chat() -> Chat:
    """Тестовый чат."""
    return Chat(id=12345, type="private")


@pytest.fixture
def mock_message(mock_bot: Bot, telegram_user: TgUser, telegram_chat: Chat) -> TgMessage:
    """Мок сообщения Telegram."""
    message = MagicMock(spec=TgMessage)
    message.message_id = 1
    message.from_user = telegram_user
    message.chat = telegram_chat
    message.bot = mock_bot
    message.answer = AsyncMock()
    message.answer_photo = AsyncMock()
    message.text = None
    message.contact = None
    return message


@pytest.fixture
def mock_contact() -> Contact:
    """Мок контакта."""
    contact = MagicMock(spec=Contact)
    contact.user_id = 67890
    contact.first_name = "New"
    contact.last_name = "Member"
    contact.phone_number = "+1234567890"
    return contact
