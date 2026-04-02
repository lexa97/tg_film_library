"""Кэш рекомендаций TMDB по film_id источника."""

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import FilmRecommendationCache


class FilmRecommendationCacheRepository:
    """CRUD по film_recommendation_cache без commit (вызывающий фиксирует транзакцию)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def delete_for_source(self, source_film_id: int) -> None:
        await self._session.execute(
            delete(FilmRecommendationCache).where(
                FilmRecommendationCache.source_film_id == source_film_id
            )
        )

    async def replace_for_source(
        self,
        source_film_id: int,
        recommendations: list[tuple[str, str]],
        fetched_at: datetime | None = None,
    ) -> None:
        """Удалить старые строки источника и вставить новый набор (ext_id, media_type)."""
        ts = fetched_at or datetime.utcnow()
        await self.delete_for_source(source_film_id)
        for position, (ext_id, media_type) in enumerate(recommendations):
            self._session.add(
                FilmRecommendationCache(
                    source_film_id=source_film_id,
                    recommended_external_id=ext_id,
                    recommended_media_type=media_type,
                    position=position,
                    fetched_at=ts,
                )
            )
        await self._session.flush()

    async def list_for_source_film_ids(
        self, source_film_ids: list[int]
    ) -> list[FilmRecommendationCache]:
        if not source_film_ids:
            return []
        result = await self._session.execute(
            select(FilmRecommendationCache).where(
                FilmRecommendationCache.source_film_id.in_(source_film_ids)
            )
        )
        return list(result.scalars().all())
