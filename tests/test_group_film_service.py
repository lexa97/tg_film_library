"""Tests for GroupFilmService."""

import pytest
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_group import UserGroupService
from app.services.film import FilmService
from app.services.group_film import GroupFilmService
from app.services.dto import FilmCreate


@pytest.mark.asyncio
async def test_add_film_to_group(db_session: AsyncSession):
    """Test adding film to group."""
    # Create user and group
    user_service = UserGroupService(db_session)
    user = await user_service.get_or_create_user(
        telegram_user_id=12345,
        username="user",
        first_name="User"
    )
    
    group = await user_service.create_group(
        name="Test Group",
        admin_user_id=user.id
    )
    
    # Create film service with mock provider
    mock_provider = AsyncMock()
    film_service = FilmService(db_session, mock_provider)
    
    # Create group film service
    group_film_service = GroupFilmService(db_session, film_service)
    
    # Add film to group
    film_data = FilmCreate(
        external_id="550",
        source="tmdb",
        title="Бойцовский клуб",
        title_original="Fight Club",
        year=1999,
        description="Test description"
    )
    
    group_film = await group_film_service.add_film_to_group(
        group_id=group.id,
        film_data=film_data,
        added_by_user_id=user.id
    )
    
    assert group_film.group_id == group.id
    assert group_film.film.title == "Бойцовский клуб"
    assert group_film.added_by_user_id == user.id


@pytest.mark.asyncio
async def test_get_group_films(db_session: AsyncSession):
    """Test getting group films."""
    # Create user and group
    user_service = UserGroupService(db_session)
    user = await user_service.get_or_create_user(
        telegram_user_id=12345,
        username="user",
        first_name="User"
    )
    
    group = await user_service.create_group(
        name="Test Group",
        admin_user_id=user.id
    )
    
    # Create services
    mock_provider = AsyncMock()
    film_service = FilmService(db_session, mock_provider)
    group_film_service = GroupFilmService(db_session, film_service)
    
    # Add film
    film_data = FilmCreate(
        external_id="550",
        source="tmdb",
        title="Бойцовский клуб",
        year=1999
    )
    
    await group_film_service.add_film_to_group(
        group_id=group.id,
        film_data=film_data,
        added_by_user_id=user.id
    )
    
    # Get films
    films, total = await group_film_service.get_group_films(
        group_id=group.id,
        limit=10,
        offset=0
    )
    
    assert total == 1
    assert len(films) == 1
    assert films[0].film.title == "Бойцовский клуб"


@pytest.mark.asyncio
async def test_mark_watched(db_session: AsyncSession):
    """Test marking film as watched."""
    # Create user and group
    user_service = UserGroupService(db_session)
    user = await user_service.get_or_create_user(
        telegram_user_id=12345,
        username="user",
        first_name="User"
    )
    
    group = await user_service.create_group(
        name="Test Group",
        admin_user_id=user.id
    )
    
    # Create services
    mock_provider = AsyncMock()
    film_service = FilmService(db_session, mock_provider)
    group_film_service = GroupFilmService(db_session, film_service)
    
    # Add film
    film_data = FilmCreate(
        external_id="550",
        source="tmdb",
        title="Бойцовский клуб"
    )
    
    group_film = await group_film_service.add_film_to_group(
        group_id=group.id,
        film_data=film_data,
        added_by_user_id=user.id
    )
    
    # Check not watched
    is_watched_before = await group_film_service.is_watched(group_film.id)
    assert is_watched_before is False
    
    # Mark as watched
    await group_film_service.mark_watched(
        group_film_id=group_film.id,
        marked_by_user_id=user.id
    )
    
    # Check watched
    is_watched_after = await group_film_service.is_watched(group_film.id)
    assert is_watched_after is True
