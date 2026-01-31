"""Tests for FilmService."""

import pytest
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.film import FilmService
from app.services.dto import FilmCreate


@pytest.mark.asyncio
async def test_get_or_create_film(db_session: AsyncSession, mock_tmdb_search_results):
    """Test film creation."""
    # Mock search provider
    mock_provider = AsyncMock()
    mock_provider.search.return_value = mock_tmdb_search_results
    
    service = FilmService(db_session, mock_provider)
    
    # Create film data
    film_data = FilmCreate(
        external_id="550",
        source="tmdb",
        title="Бойцовский клуб",
        title_original="Fight Club",
        year=1999,
        description="Test description",
        poster_url="https://example.com/poster.jpg"
    )
    
    # Create film
    film = await service.get_or_create_film(film_data)
    
    assert film.external_id == "550"
    assert film.title == "Бойцовский клуб"
    assert film.year == 1999
    
    # Get same film again (should return existing)
    film2 = await service.get_or_create_film(film_data)
    assert film2.id == film.id


@pytest.mark.asyncio
async def test_search_films(db_session: AsyncSession, mock_tmdb_search_results):
    """Test film search."""
    # Mock search provider
    mock_provider = AsyncMock()
    mock_provider.search.return_value = mock_tmdb_search_results
    
    service = FilmService(db_session, mock_provider)
    
    # Search films
    results = await service.search_films("Fight Club", language="ru")
    
    assert len(results) == 1
    assert results[0].title == "Бойцовский клуб"
    mock_provider.search.assert_called_once_with("Fight Club", "ru")
