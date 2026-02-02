import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message

from app.handlers.start import cmd_start
from app.db.models import User, Group


@pytest.mark.asyncio
async def test_start_without_groups(
    mock_message: Message,
    mock_session: AsyncMock,
):
    """Тест команды /start когда пользователь не в группах."""
    mock_user = User(
        id=1,
        telegram_user_id=12345,
        username="testuser",
        first_name="Test",
        last_name="User",
    )
    mock_svc = MagicMock()
    mock_svc.get_or_create_user = AsyncMock(return_value=mock_user)
    mock_svc.get_user_groups = AsyncMock(return_value=[])

    await cmd_start(mock_message, mock_session, mock_svc)

    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "Вас ещё нет ни в одной группе" in call_args


@pytest.mark.asyncio
async def test_start_with_groups(
    mock_message: Message,
    mock_session: AsyncMock,
):
    """Тест команды /start когда пользователь в группах."""
    mock_user = User(
        id=1,
        telegram_user_id=12345,
        username="testuser",
        first_name="Test",
        last_name="User",
    )
    mock_group = Group(id=1, name="Test Group", admin_user_id=1)
    mock_group.name = "Test Group"

    mock_svc = MagicMock()
    mock_svc.get_or_create_user = AsyncMock(return_value=mock_user)
    mock_svc.get_user_groups = AsyncMock(return_value=[mock_group])

    await cmd_start(mock_message, mock_session, mock_svc)

    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "Test Group" in call_args
    assert "/list" in call_args
