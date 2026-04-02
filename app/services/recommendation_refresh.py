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
    skipped_non_tmdb = 0

    logger.info(
        "recommendation cache refresh: уникальных film_id в списках групп: %s",
        len(film_ids),
    )
    if not film_ids:
        logger.info(
            "recommendation cache refresh: нечего обновлять — в group_films нет записей"
        )
        return 0, 0

    for fid in film_ids:
        film = await session.get(Film, fid)
        if not film:
            continue
        if (film.source or "").lower() != "tmdb":
            skipped_non_tmdb += 1
            continue
        media_type = (film.media_type or "movie").strip() or "movie"
        recs = await search.fetch_recommendations(film.external_id, media_type)
        if recs is None:
            failed += 1
            logger.warning(
                "recommendation cache: film_id=%s external_id=%s type=%s — TMDB error, старый кэш для источника не трогаем",
                fid,
                film.external_id,
                media_type,
            )
            await asyncio.sleep(delay_between_requests_sec)
            continue
        await cache_repo.replace_for_source(fid, recs)
        ok += 1
        if not recs:
            logger.debug(
                "recommendation cache: film_id=%s — TMDB вернул 0 рекомендаций, кэш очищен",
                fid,
            )
        await asyncio.sleep(delay_between_requests_sec)

    logger.info(
        "recommendation cache refresh finished: updated=%s failed_tmdb=%s skipped_non_tmdb=%s",
        ok,
        failed,
        skipped_non_tmdb,
    )
    return ok, failed
