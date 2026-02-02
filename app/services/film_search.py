"""
Абстракция поисковика фильмов. Реализация под TMDB; при расширении — другие провайдеры.
Маппинг ответов API в DTO только здесь, не в хендлерах.
"""
from abc import ABC, abstractmethod

from app.schemas import FilmCreate, FilmSearchResult


class BaseFilmSearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, language: str = "ru-RU") -> list[FilmSearchResult]:
        """Поиск фильмов/сериалов. Возвращает до N результатов (например, 5)."""
        pass

    @abstractmethod
    async def fetch_film(self, external_id: str, media_type: str) -> FilmCreate | None:
        """Получить полные данные фильма/сериала по id для сохранения в БД."""
        pass
