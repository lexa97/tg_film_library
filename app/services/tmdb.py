from typing import Any

import httpx

from app.config import get_settings


TMDB_BASE = "https://api.themoviedb.org/3"
POSTER_BASE = "https://image.tmdb.org/t/p/w500"


async def search_multi(query: str, language: str = "ru-RU", page: int = 1) -> list[dict[str, Any]]:
    """Поиск фильмов и сериалов. Возвращает до 5 результатов."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{TMDB_BASE}/search/multi",
            params={
                "api_key": settings.TMDB_API_KEY,
                "query": query,
                "language": language,
                "page": page,
                "include_adult": False,
            },
            timeout=10.0,
        )
        r.raise_for_status()
        data = r.json()
    results = data.get("results", [])
    # Только movie и tv
    filtered = [x for x in results if x.get("media_type") in ("movie", "tv")][:5]
    return filtered


def format_poster_url(path: str | None) -> str | None:
    if not path:
        return None
    return f"{POSTER_BASE}{path}"


async def fetch_movie_or_tv(external_id: str, media_type: str) -> dict[str, Any] | None:
    """Получить данные фильма/сериала по id для сохранения в БД."""
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
    title = item.get("title") or item.get("name") or "Без названия"
    title_original = item.get("original_title") or item.get("original_name")
    release_date = item.get("release_date") or item.get("first_air_date") or ""
    year = int(release_date[:4]) if len(release_date) >= 4 else None
    poster_path = item.get("poster_path")
    overview = (item.get("overview") or "")[:2000]
    return {
        "external_id": str(item["id"]),
        "source": "tmdb",
        "title": title,
        "title_original": title_original,
        "year": year,
        "description": overview or None,
        "poster_url": format_poster_url(poster_path),
        "media_type": media_type,
    }


def result_to_film_data(item: dict[str, Any]) -> dict[str, Any]:
    """Преобразует элемент ответа TMDB в данные для сохранения в БД."""
    media_type = item.get("media_type", "movie")
    title = item.get("title") or item.get("name") or "Без названия"
    title_original = item.get("original_title") or item.get("original_name")
    release_date = item.get("release_date") or item.get("first_air_date") or ""
    year = int(release_date[:4]) if len(release_date) >= 4 else None
    poster_path = item.get("poster_path")
    overview = (item.get("overview") or "")[:2000]
    return {
        "external_id": str(item["id"]),
        "source": "tmdb",
        "title": title,
        "title_original": title_original,
        "year": year,
        "description": overview or None,
        "poster_url": format_poster_url(poster_path),
        "media_type": media_type,
    }
