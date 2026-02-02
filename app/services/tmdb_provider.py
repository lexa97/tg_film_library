"""
Реализация поисковика фильмов через TMDB API.
Маппинг ответов TMDB в Pydantic DTO только здесь.
"""
from typing import Any

import httpx

from app.config import get_settings
from app.schemas import FilmCreate, FilmSearchResult
from app.services.film_search import BaseFilmSearchProvider

TMDB_BASE = "https://api.themoviedb.org/3"
POSTER_BASE = "https://image.tmdb.org/t/p/w500"
MAX_SEARCH_RESULTS = 5


def _poster_url(path: str | None) -> str | None:
    if not path:
        return None
    return f"{POSTER_BASE}{path}"


def _item_to_search_result(item: dict[str, Any]) -> FilmSearchResult:
    media_type = item.get("media_type", "movie")
    title = item.get("title") or item.get("name") or "Без названия"
    release_date = item.get("release_date") or item.get("first_air_date") or ""
    year = int(release_date[:4]) if len(release_date) >= 4 else None
    overview = (item.get("overview") or "")[:2000] or None
    return FilmSearchResult(
        external_id=str(item["id"]),
        source="tmdb",
        title=title,
        year=year,
        description=overview,
        poster_url=_poster_url(item.get("poster_path")),
        media_type=media_type,
    )


def _item_to_film_create(item: dict[str, Any], media_type: str) -> FilmCreate:
    title = item.get("title") or item.get("name") or "Без названия"
    title_original = item.get("original_title") or item.get("original_name")
    release_date = item.get("release_date") or item.get("first_air_date") or ""
    year = int(release_date[:4]) if len(release_date) >= 4 else None
    overview = (item.get("overview") or "")[:2000] or None
    return FilmCreate(
        external_id=str(item["id"]),
        source="tmdb",
        title=title,
        title_original=title_original,
        year=year,
        description=overview,
        poster_url=_poster_url(item.get("poster_path")),
        media_type=media_type,
    )


class TMDBFilmSearch(BaseFilmSearchProvider):
    """Провайдер поиска фильмов и сериалов через TMDB."""

    async def search(self, query: str, language: str = "ru-RU") -> list[FilmSearchResult]:
        settings = get_settings()
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{TMDB_BASE}/search/multi",
                params={
                    "api_key": settings.TMDB_API_KEY,
                    "query": query,
                    "language": language,
                    "page": 1,
                    "include_adult": False,
                },
                timeout=10.0,
            )
            r.raise_for_status()
            data = r.json()
        results = data.get("results", [])
        filtered = [x for x in results if x.get("media_type") in ("movie", "tv")][:MAX_SEARCH_RESULTS]
        return [_item_to_search_result(x) for x in filtered]

    async def fetch_film(self, external_id: str, media_type: str) -> FilmCreate | None:
        settings = get_settings()
        endpoint = "movie" if media_type == "movie" else "tv"
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{TMDB_BASE}/{endpoint}/{external_id}",
                params={
                    "api_key": settings.TMDB_API_KEY,
                    "language": "ru-RU",
                },
                timeout=10.0,
            )
            if r.status_code != 200:
                return None
            item = r.json()
        return _item_to_film_create(item, media_type)
