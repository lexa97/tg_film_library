import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, Contact

from app.handlers.group import on_contact
from app.db.models import User, Group


@pytest.mark.asyncio
async def test_contact_no_group(
    mock_message: Message,
    mock_session: AsyncMock,
    mock_contact: Contact,
    mocker,
):
    """Тест обработки контакта когда пользователь не в группе."""
    mock_message.contact = mock_contact
    
    # Мокируем сервисы
    mock_user = User(
        id=1,
        telegram_user_id=12345,
        username="testuser",
        first_name="Test",
        last_name="User",
    )
    
    mocker.patch("app.handlers.group.get_or_create_user", new_callable=AsyncMock, return_value=mock_user)
    mocker.patch("app.handlers.group.get_user_group", new_callable=AsyncMock, return_value=None)
    
    # Вызываем хендлер
    await on_contact(mock_message, mock_session)
    
    # Проверяем сообщение об ошибке
    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "Сначала создайте группу" in call_args or "вы должны быть в группе" in call_args


@pytest.mark.asyncio
async def test_contact_not_admin(
    mock_message: Message,
    mock_session: AsyncMock,
    mock_contact: Contact,
    mocker,
):
    """Тест обработки контакта когда пользователь не админ."""
    mock_message.contact = mock_contact
    
    # Мокируем сервисы
    mock_user = User(
        id=1,
        telegram_user_id=12345,
        username="testuser",
        first_name="Test",
        last_name="User",
    )
    
    mock_group = Group(id=1, name="Test Group", admin_user_id=2)
    
    mocker.patch("app.handlers.group.get_or_create_user", return_value=mock_user)
    mocker.patch("app.handlers.group.get_user_group", return_value=mock_group)
    mocker.patch("app.handlers.group.is_group_admin", return_value=False)
    
    # Вызываем хендлер
    await on_contact(mock_message, mock_session)
    
    # Проверяем сообщение об ошибке
    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "только админ" in call_args


@pytest.mark.asyncio
async def test_contact_user_not_found(
    mock_message: Message,
    mock_session: AsyncMock,
    mock_contact: Contact,
    mocker,
):
    """Тест обработки контакта когда пользователь не найден."""
    mock_message.contact = mock_contact
    
    # Мокируем сервисы
    mock_user = User(
        id=1,
        telegram_user_id=12345,
        username="testuser",
        first_name="Test",
        last_name="User",
    )
    
    mock_group = Group(id=1, name="Test Group", admin_user_id=1)
    
    mocker.patch("app.handlers.group.get_or_create_user", new_callable=AsyncMock, return_value=mock_user)
    mocker.patch("app.handlers.group.get_user_group", new_callable=AsyncMock, return_value=mock_group)
    mocker.patch("app.handlers.group.is_group_admin", new_callable=AsyncMock, return_value=True)
    mocker.patch("app.handlers.group.get_user_by_telegram_id", new_callable=AsyncMock, return_value=None)
    
    # Вызываем хендлер
    await on_contact(mock_message, mock_session)
    
    # Проверяем сообщение об ошибке
    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "не нажимал /start" in call_args or "запустить бота" in call_args


@pytest.mark.asyncio
async def test_contact_success(
    mock_message: Message,
    mock_session: AsyncMock,
    mock_contact: Contact,
    mocker,
):
    """Тест успешного добавления пользователя в группу."""
    mock_message.contact = mock_contact
    
    # Мокируем сервисы
    mock_user = User(
        id=1,
        telegram_user_id=12345,
        username="testuser",
        first_name="Test",
        last_name="User",
    )
    
    mock_new_user = User(
        id=2,
        telegram_user_id=67890,
        username="newuser",
        first_name="New",
        last_name="Member",
    )
    
    mock_group = Group(id=1, name="Test Group", admin_user_id=1)
    
    from app.db.models import GroupMember
    mock_member = GroupMember(id=1, group_id=1, user_id=2, role="member")
    
    mocker.patch("app.handlers.group.get_or_create_user", new_callable=AsyncMock, return_value=mock_user)
    mocker.patch("app.handlers.group.get_user_group", new_callable=AsyncMock, return_value=mock_group)
    mocker.patch("app.handlers.group.is_group_admin", new_callable=AsyncMock, return_value=True)
    mocker.patch("app.handlers.group.get_user_by_telegram_id", new_callable=AsyncMock, return_value=mock_new_user)
    mocker.patch("app.handlers.group.add_member_to_group", new_callable=AsyncMock, return_value=mock_member)
    
    # Вызываем хендлер
    await on_contact(mock_message, mock_session)
    
    # Проверяем успешное сообщение
    assert mock_message.answer.call_count >= 1
    call_args = mock_message.answer.call_args[0][0]
    assert "добавлен в группу" in call_args
    assert "Test Group" in call_args
    
    # Проверяем, что отправлено уведомление новому пользователю
    mock_message.bot.send_message.assert_called_once()
