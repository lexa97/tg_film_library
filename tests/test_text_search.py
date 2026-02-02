import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message

from app.handlers.film_search import on_text_search
from app.db.models import Group
from app.schemas import FilmSearchResult


@pytest.mark.asyncio
async def test_text_search_no_group(
    mock_message: Message,
    mock_session: AsyncMock,
):
    """Тест поиска когда пользователь не в группе."""
    mock_message.text = "Inception"

    mock_user_svc = MagicMock()
    mock_user_svc.get_user_group = AsyncMock(return_value=None)
    mock_film_search = MagicMock()

    await on_text_search(mock_message, mock_session, mock_user_svc, mock_film_search)

    mock_message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_text_search_no_results(
    mock_message: Message,
    mock_session: AsyncMock,
):
    """Тест поиска когда ничего не найдено."""
    mock_message.text = "NonexistentMovie12345"

    mock_user_svc = MagicMock()
    mock_user_svc.get_user_group = AsyncMock(return_value=Group(id=1, name="Test Group", admin_user_id=1))
    mock_film_search = MagicMock()
    mock_film_search.search = AsyncMock(return_value=[])

    await on_text_search(mock_message, mock_session, mock_user_svc, mock_film_search)

    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "Ничего не найдено" in call_args


@pytest.mark.asyncio
async def test_text_search_success(
    mock_message: Message,
    mock_session: AsyncMock,
):
    """Тест успешного поиска фильма."""
    mock_message.text = "Inception"

    mock_user_svc = MagicMock()
    mock_user_svc.get_user_group = AsyncMock(return_value=Group(id=1, name="Test Group", admin_user_id=1))
    mock_film_search = MagicMock()
    mock_film_search.search = AsyncMock(
        return_value=[
            FilmSearchResult(
                external_id="27205",
                source="tmdb",
                title="Inception",
                year=2010,
                description="A skilled thief is given a chance at redemption...",
                poster_url="https://image.tmdb.org/t/p/w500/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg",
                media_type="movie",
            )
        ]
    )

    await on_text_search(mock_message, mock_session, mock_user_svc, mock_film_search)

    assert mock_message.answer.call_count >= 1 or mock_message.answer_photo.call_count >= 1
    mock_message.bot.send_chat_action.assert_called_once_with(mock_message.chat.id, "typing")

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
):
    """Тест что короткий запрос игнорируется."""
    mock_message.text = "A"

    mock_user_svc = MagicMock()
    mock_user_svc.get_user_group = AsyncMock(return_value=Group(id=1, name="Test Group", admin_user_id=1))
    mock_film_search = MagicMock()

    await on_text_search(mock_message, mock_session, mock_user_svc, mock_film_search)

    mock_message.answer.assert_not_called()
    mock_message.bot.send_chat_action.assert_not_called()
