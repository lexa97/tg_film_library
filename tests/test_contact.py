import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, Contact

from app.handlers.group import on_contact
from app.db.models import User, Group
from app.schemas import AddMemberResult


@pytest.mark.asyncio
async def test_contact_no_group(
    mock_message: Message,
    mock_session: AsyncMock,
    mock_contact: Contact,
):
    """Тест обработки контакта когда пользователь не в группе."""
    mock_message.contact = mock_contact

    mock_svc = MagicMock()
    mock_svc.add_member_by_contact = AsyncMock(
        return_value=AddMemberResult(success=False, error="Сначала создайте группу (команда /newgroup) или вы должны быть в группе.")
    )

    await on_contact(mock_message, mock_session, mock_svc)

    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "Сначала создайте группу" in call_args or "вы должны быть в группе" in call_args


@pytest.mark.asyncio
async def test_contact_not_admin(
    mock_message: Message,
    mock_session: AsyncMock,
    mock_contact: Contact,
):
    """Тест обработки контакта когда пользователь не админ."""
    mock_message.contact = mock_contact

    mock_svc = MagicMock()
    mock_svc.add_member_by_contact = AsyncMock(
        return_value=AddMemberResult(success=False, error="Добавлять участников может только админ группы.")
    )

    await on_contact(mock_message, mock_session, mock_svc)

    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "только админ" in call_args


@pytest.mark.asyncio
async def test_contact_user_not_found(
    mock_message: Message,
    mock_session: AsyncMock,
    mock_contact: Contact,
):
    """Тест обработки контакта когда пользователь не найден."""
    mock_message.contact = mock_contact

    mock_svc = MagicMock()
    mock_svc.add_member_by_contact = AsyncMock(
        return_value=AddMemberResult(success=False, error="Этот пользователь ещё не нажимал /start у бота. Попросите его сначала запустить бота.")
    )

    await on_contact(mock_message, mock_session, mock_svc)

    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "не нажимал /start" in call_args or "запустить бота" in call_args


@pytest.mark.asyncio
async def test_contact_success(
    mock_message: Message,
    mock_session: AsyncMock,
    mock_contact: Contact,
):
    """Тест успешного добавления пользователя в группу."""
    mock_message.contact = mock_contact

    mock_svc = MagicMock()
    mock_svc.add_member_by_contact = AsyncMock(
        return_value=AddMemberResult(
            success=True,
            group_name="Test Group",
            new_member_display_name="New Member",
        )
    )

    await on_contact(mock_message, mock_session, mock_svc)

    assert mock_message.answer.call_count >= 1
    call_args = mock_message.answer.call_args[0][0]
    assert "добавлен в группу" in call_args
    assert "Test Group" in call_args
