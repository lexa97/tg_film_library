import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message

from app.handlers.film_search import on_text_search
from app.db.models import Group


@pytest.mark.asyncio
async def test_text_search_no_group(
    mock_message: Message,
    mock_session: AsyncMock,
    mocker,
):
    """Тест поиска когда пользователь не в группе."""
    mock_message.text = "Inception"
    
    # Мокируем сервисы
    mocker.patch("app.handlers.film_search.get_user_group", new_callable=AsyncMock, return_value=None)
    
    # Вызываем хендлер
    await on_text_search(mock_message, mock_session)
    
    # Хендлер должен вернуться без ответа (не в группе)
    mock_message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_text_search_no_results(
    mock_message: Message,
    mock_session: AsyncMock,
    mocker,
):
    """Тест поиска когда ничего не найдено."""
    mock_message.text = "NonexistentMovie12345"
    
    # Мокируем сервисы
    mock_group = Group(id=1, name="Test Group", admin_user_id=1)
    
    mocker.patch("app.handlers.film_search.get_user_group", return_value=mock_group)
    mocker.patch("app.handlers.film_search.search_multi", return_value=[])
    
    # Вызываем хендлер
    await on_text_search(mock_message, mock_session)
    
    # Проверяем сообщение "ничего не найдено"
    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "Ничего не найдено" in call_args


@pytest.mark.asyncio
async def test_text_search_success(
    mock_message: Message,
    mock_session: AsyncMock,
    mocker,
):
    """Тест успешного поиска фильма."""
    mock_message.text = "Inception"
    
    # Мокируем сервисы
    mock_group = Group(id=1, name="Test Group", admin_user_id=1)
    
    # Мокируем ответ TMDB
    mock_tmdb_result = [
        {
            "id": 27205,
            "media_type": "movie",
            "title": "Inception",
            "original_title": "Inception",
            "release_date": "2010-07-16",
            "overview": "A skilled thief is given a chance at redemption...",
            "poster_path": "/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg",
        }
    ]
    
    mocker.patch("app.handlers.film_search.get_user_group", new_callable=AsyncMock, return_value=mock_group)
    mocker.patch("app.handlers.film_search.search_multi", new_callable=AsyncMock, return_value=mock_tmdb_result)
    
    # Вызываем хендлер
    await on_text_search(mock_message, mock_session)
    
    # Проверяем, что отправлено сообщение с результатами
    assert mock_message.answer.call_count >= 1 or mock_message.answer_photo.call_count >= 1
    
    # Проверяем, что отправлен action "typing"
    mock_message.bot.send_chat_action.assert_called_once_with(mock_message.chat.id, "typing")
    
    # Проверяем, что в ответе есть название фильма
    if mock_message.answer.call_count > 0:
        call_args = mock_message.answer.call_args[0][0]
        assert "Inception" in call_args
    elif mock_message.answer_photo.call_count > 0:
        caption = mock_message.answer_photo.call_args[1].get("caption", "")
        assert "Inception" in caption


@pytest.mark.asyncio
async def test_text_search_short_query(
    mock_message: Message,
    mock_session: AsyncMock,
    mocker,
):
    """Тест что короткий запрос игнорируется."""
    mock_message.text = "A"
    
    # Мокируем сервисы
    mock_group = Group(id=1, name="Test Group", admin_user_id=1)
    
    mocker.patch("app.handlers.film_search.get_user_group", new_callable=AsyncMock, return_value=mock_group)
    
    # Вызываем хендлер
    await on_text_search(mock_message, mock_session)
    
    # Хендлер должен вернуться без ответа (слишком короткий запрос)
    mock_message.answer.assert_not_called()
    mock_message.bot.send_chat_action.assert_not_called()
