"""Фоновое обновление кэша film_recommendation_cache."""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Film
from app.db.repositories import FilmRecommendationCacheRepository, GroupFilmRepository
from app.services.tmdb import TMDBFilmSearch

logger = logging.getLogger(__name__)


async def refresh_recommendation_cache_for_all_sources(
    session: AsyncSession,
    search: TMDBFilmSearch,
    delay_between_requests_sec: float = 0.35,
) -> tuple[int, int]:
    """
    Для каждого film_id из group_films (уникально) подтянуть recommendations в кэш.

    Returns:
        (обработано источников, пропущено из-за ошибок TMDB)
    """
    gf_repo = GroupFilmRepository(session)
    cache_repo = FilmRecommendationCacheRepository(session)
    film_ids = await gf_repo.distinct_film_ids_in_use()
    ok = 0
    failed = 0

    for fid in film_ids:
        film = await session.get(Film, fid)
        if not film or film.source != "tmdb":
            continue
        media_type = film.media_type or "movie"
        recs = await search.fetch_recommendations(film.external_id, media_type)
        if recs is None:
            failed += 1
            logger.warning(
                "recommendation cache: skip refresh for film_id=%s (TMDB error), keep old cache",
                fid,
            )
            await asyncio.sleep(delay_between_requests_sec)
            continue
        await cache_repo.replace_for_source(fid, recs)
        ok += 1
        await asyncio.sleep(delay_between_requests_sec)

    logger.info(
        "recommendation cache refresh finished: sources_updated=%s sources_failed=%s",
        ok,
        failed,
    )
    return ok, failed
