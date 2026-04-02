"""Подборка «похожих» по кэшу TMDB recommendations и просмотренным в группе."""

import logging
from enum import Enum

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import FilmRecommendationCacheRepository, GroupFilmRepository
from app.services.base import BaseFilmSearchProvider
from app.services.dto import FilmSearchResult

logger = logging.getLogger(__name__)

# Вес с позиции TMDB: верх списка сильнее; уменьшает перекос «что везде в хвосте рекомендаций».
def _recommendation_row_weight(position: int) -> int:
    return max(1, 14 - min(position, 13))


class RelativeOutcomeKind(str, Enum):
    OK = "ok"
    NO_WATCHED = "no_watched"
    CACHE_EMPTY = "cache_empty"
    NO_CANDIDATES = "no_candidates"


class RelativeOutcome(BaseModel):
    kind: RelativeOutcomeKind
    results: list[FilmSearchResult] = Field(default_factory=list)


class RecommendationService:
    def __init__(self, session: AsyncSession, search: BaseFilmSearchProvider) -> None:
        self._session = session
        self._search = search
        self._cache = FilmRecommendationCacheRepository(session)
        self._group_films = GroupFilmRepository(session)

    async def build_relative_suggestions(
        self, group_id: int, limit: int = 5
    ) -> RelativeOutcome:
        watched_ids = await self._group_films.watched_film_ids_for_group(group_id)
        if not watched_ids:
            return RelativeOutcome(kind=RelativeOutcomeKind.NO_WATCHED)

        rows = await self._cache.list_for_source_film_ids(watched_ids)
        if not rows:
            return RelativeOutcome(kind=RelativeOutcomeKind.CACHE_EMPTY)

        media_list = await self._group_films.watched_film_media_types(group_id)
        movies_n = sum(1 for m in media_list if (m or "movie") == "movie")
        tvs_n = len(media_list) - movies_n
        if movies_n > tvs_n:
            allowed_types = {"movie"}
        elif tvs_n > movies_n:
            allowed_types = {"tv"}
        else:
            allowed_types = {"movie", "tv"}

        def _aggregate(filter_types: set[str] | None) -> dict[tuple[str, str], int]:
            acc: dict[tuple[str, str], int] = {}
            for r in rows:
                mt = (r.recommended_media_type or "movie").strip() or "movie"
                if filter_types is not None and mt not in filter_types:
                    continue
                key = (r.recommended_external_id, mt)
                pos = getattr(r, "position", 0) or 0
                acc[key] = acc.get(key, 0) + _recommendation_row_weight(pos)
            return acc

        scores = _aggregate(allowed_types)
        if not scores:
            scores = _aggregate(None)

        in_group = await self._group_films.list_group_external_keys(group_id)
        ranked = sorted(
            scores.items(),
            key=lambda kv: (-kv[1], kv[0][0], kv[0][1]),
        )
        ordered_keys = [k for k, _ in ranked if k not in in_group]

        results: list[FilmSearchResult] = []
        for ext_id, media_type in ordered_keys:
            if len(results) >= limit:
                break
            detail = await self._search.get_details(ext_id, media_type)
            if detail:
                results.append(detail)

        if not results:
            return RelativeOutcome(kind=RelativeOutcomeKind.NO_CANDIDATES)

        return RelativeOutcome(kind=RelativeOutcomeKind.OK, results=results)
