"""
Сервис списка «к просмотру» и отметки «просмотрен»: подтверждение фильма, список группы, деталь, отметка.
Вся бизнес-логика и уведомления участникам — здесь.
"""
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Film, GroupFilm
from app.db.repositories import (
    FilmRepository,
    GroupFilmRepository,
    GroupMemberRepository,
    GroupRepository,
    UserRepository,
    WatchedRepository,
)
from app.schemas import AddFilmResult, MarkWatchedResult
from app.services.film_search import BaseFilmSearchProvider


class GroupFilmService:
    def __init__(
        self,
        user_repo: UserRepository,
        group_repo: GroupRepository,
        film_repo: FilmRepository,
        group_film_repo: GroupFilmRepository,
        watched_repo: WatchedRepository,
        group_member_repo: GroupMemberRepository,
        film_search: BaseFilmSearchProvider,
    ) -> None:
        self._user = user_repo
        self._group = group_repo
        self._film = film_repo
        self._group_film = group_film_repo
        self._watched = watched_repo
        self._member = group_member_repo
        self._search = film_search

    async def confirm_and_add_film(
        self,
        session: AsyncSession,
        group_id: int,
        telegram_user_id: int,
        external_id: str,
        media_type: str,
        bot: Bot | None = None,
    ) -> AddFilmResult:
        """Подтвердить выбор и добавить фильм в группу. Уведомления участникам — внутри."""
        film_data = await self._search.fetch_film(external_id, media_type)
        if not film_data:
            return AddFilmResult(success=False, error="Не удалось загрузить данные фильма.")
        film = await self._film.find_by_external(session, external_id, film_data.source)
        if not film:
            film = await self._film.create(session, film_data)
        user = await self._user.get_or_create(session, telegram_user_id)
        await self._group_film.add(session, group_id, film.id, user.id)
        group = await self._group.get_by_id(session, group_id)
        group_name = group.name if group else ""
        if bot:
            member_ids = await self._member.get_member_telegram_ids(session, group_id)
            year_suffix = f" ({film.year})" if film.year else ""
            for uid in member_ids:
                if uid == telegram_user_id:
                    continue
                try:
                    await bot.send_message(
                        uid,
                        f"В список группы «{group_name}» добавлен фильм: {film.title}{year_suffix}.",
                    )
                except Exception:
                    pass
        return AddFilmResult(
            success=True,
            film_title=film.title,
            film_year=film.year,
            group_name=group_name,
        )

    async def get_group_films(
        self,
        session: AsyncSession,
        group_id: int,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[tuple[GroupFilm, Film, bool]]:
        return await self._group_film.get_list(session, group_id, search=search, limit=limit, offset=offset)

    async def get_group_film_detail(
        self, session: AsyncSession, group_film_id: int, group_id: int
    ) -> tuple[GroupFilm, Film, bool] | None:
        row = await self._group_film.get_by_id(session, group_film_id, group_id)
        if not row:
            return None
        gf, film = row
        watched = await self._watched.is_watched(session, gf.id)
        return (gf, film, watched)

    async def mark_watched(
        self,
        session: AsyncSession,
        group_film_id: int,
        group_id: int,
        telegram_user_id: int,
        bot: Bot | None = None,
    ) -> MarkWatchedResult:
        """Отметить фильм просмотренным. Уведомления участникам — внутри."""
        row = await self._group_film.get_by_id(session, group_film_id, group_id)
        if not row:
            return MarkWatchedResult(success=False, error="Фильм не найден.")
        gf, film = row
        user = await self._user.get_or_create(session, telegram_user_id)
        await self._watched.mark(session, gf.id, user.id)
        group = await self._group.get_by_id(session, group_id)
        group_name = group.name if group else ""
        if bot:
            member_ids = await self._member.get_member_telegram_ids(session, group_id)
            for uid in member_ids:
                if uid == telegram_user_id:
                    continue
                try:
                    await bot.send_message(
                        uid,
                        f"В группе «{group_name}» фильм «{film.title}» отмечен как просмотренный.",
                    )
                except Exception:
                    pass
        return MarkWatchedResult(
            success=True,
            group_name=group_name,
            film_title=film.title,
        )