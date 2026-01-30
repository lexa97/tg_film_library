import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message

from app.handlers.start import cmd_start
from app.db.models import User, Group


@pytest.mark.asyncio
async def test_start_without_groups(
    mock_message: Message,
    mock_session: AsyncMock,
    mocker,
):
    """Тест команды /start когда пользователь не в группах."""
    # Мокируем сервисы
    mock_user = User(
        id=1,
        telegram_user_id=12345,
        username="testuser",
        first_name="Test",
        last_name="User",
    )
    
    mocker.patch("app.handlers.start.get_or_create_user", return_value=mock_user)
    mocker.patch("app.handlers.start.get_user_groups", return_value=[])
    
    # Вызываем хендлер
    await cmd_start(mock_message, mock_session)
    
    # Проверяем, что отправлено сообщение о том, что пользователь не в группах
    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "Вас ещё нет ни в одной группе" in call_args


@pytest.mark.asyncio
async def test_start_with_groups(
    mock_message: Message,
    mock_session: AsyncMock,
    mocker,
):
    """Тест команды /start когда пользователь в группах."""
    # Мокируем сервисы
    mock_user = User(
        id=1,
        telegram_user_id=12345,
        username="testuser",
        first_name="Test",
        last_name="User",
    )
    
    mock_group = Group(id=1, name="Test Group", admin_user_id=1)
    mock_group.name = "Test Group"
    
    mocker.patch("app.handlers.start.get_or_create_user", new_callable=AsyncMock, return_value=mock_user)
    mocker.patch("app.handlers.start.get_user_groups", new_callable=AsyncMock, return_value=[mock_group])
    
    # Вызываем хендлер
    await cmd_start(mock_message, mock_session)
    
    # Проверяем, что отправлено сообщение со списком групп
    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "Test Group" in call_args
    assert "/list" in call_args
