"""
Репозитории: доступ к БД по одной сущности. Без бизнес-логики, только CRUD.
Все методы принимают session первым аргументом.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Film, Group, GroupFilm, GroupMember, User, Watched
from app.schemas import FilmCreate


class UserRepository:
    async def get_by_telegram_id(self, session: AsyncSession, telegram_user_id: int) -> User | None:
        result = await session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        session: AsyncSession,
        telegram_user_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        user = await self.get_by_telegram_id(session, telegram_user_id)
        if user:
            if username is not None:
                user.username = username
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            return user
        user = User(
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        session.add(user)
        await session.flush()
        return user


class GroupRepository:
    async def create(self, session: AsyncSession, name: str, admin_user_id: int) -> Group:
        group = Group(name=name.strip(), admin_user_id=admin_user_id)
        session.add(group)
        await session.flush()
        return group

    async def get_by_id(self, session: AsyncSession, group_id: int) -> Group | None:
        result = await session.execute(select(Group).where(Group.id == group_id))
        return result.scalar_one_or_none()


class GroupMemberRepository:
    async def get_user_groups(self, session: AsyncSession, telegram_user_id: int) -> list[Group]:
        result = await session.execute(
            select(Group)
            .join(GroupMember, Group.id == GroupMember.group_id)
            .join(User, GroupMember.user_id == User.id)
            .where(User.telegram_user_id == telegram_user_id)
        )
        return list(result.scalars().all())

    async def add_member(
        self, session: AsyncSession, group_id: int, user_id: int, role: str = "member"
    ) -> GroupMember | None:
        result = await session.execute(
            select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        )
        if result.scalar_one_or_none():
            return None
        member = GroupMember(group_id=group_id, user_id=user_id, role=role)
        session.add(member)
        await session.flush()
        return member

    async def get_member_telegram_ids(self, session: AsyncSession, group_id: int) -> list[int]:
        result = await session.execute(
            select(User.telegram_user_id)
            .join(GroupMember, User.id == GroupMember.user_id)
            .where(GroupMember.group_id == group_id)
        )
        return list(result.scalars().all())

    async def is_admin(self, session: AsyncSession, group_id: int, telegram_user_id: int) -> bool:
        result = await session.execute(
            select(GroupMember)
            .join(User, GroupMember.user_id == User.id)
            .where(GroupMember.group_id == group_id, User.telegram_user_id == telegram_user_id)
        )
        m = result.scalar_one_or_none()
        return m is not None and m.role == "admin"


class FilmRepository:
    async def find_by_external(self, session: AsyncSession, external_id: str, source: str) -> Film | None:
        result = await session.execute(
            select(Film).where(Film.external_id == external_id, Film.source == source)
        )
        return result.scalar_one_or_none()

    async def create(self, session: AsyncSession, data: FilmCreate) -> Film:
        film = Film(
            external_id=data.external_id,
            source=data.source,
            title=data.title,
            title_original=data.title_original,
            year=data.year,
            description=data.description,
            poster_url=data.poster_url,
            media_type=data.media_type,
        )
        session.add(film)
        await session.flush()
        return film


class GroupFilmRepository:
    async def add(
        self,
        session: AsyncSession,
        group_id: int,
        film_id: int,
        added_by_user_id: int,
    ) -> GroupFilm:
        gf = GroupFilm(group_id=group_id, film_id=film_id, added_by_user_id=added_by_user_id)
        session.add(gf)
        await session.flush()
        return gf

    async def get_list(
        self,
        session: AsyncSession,
        group_id: int,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[tuple[GroupFilm, Film, bool]]:
        q = (
            select(GroupFilm, Film)
            .join(Film, GroupFilm.film_id == Film.id)
            .where(GroupFilm.group_id == group_id)
            .order_by(GroupFilm.created_at.desc())
        )
        if search and search.strip():
            q = q.where(Film.title.ilike(f"%{search.strip()}%"))
        q = q.offset(offset).limit(limit)
        result = await session.execute(q)
        rows = result.all()
        group_film_ids = [gf.id for gf, _ in rows]
        watched_result = await session.execute(
            select(Watched.group_film_id).where(Watched.group_film_id.in_(group_film_ids))
        )
        watched_ids = set(watched_result.scalars().all())
        return [(gf, film, gf.id in watched_ids) for gf, film in rows]

    async def get_by_id(
        self, session: AsyncSession, group_film_id: int, group_id: int
    ) -> tuple[GroupFilm, Film] | None:
        result = await session.execute(
            select(GroupFilm, Film)
            .join(Film, GroupFilm.film_id == Film.id)
            .where(GroupFilm.id == group_film_id, GroupFilm.group_id == group_id)
        )
        return result.one_or_none()


class WatchedRepository:
    async def mark(self, session: AsyncSession, group_film_id: int, user_id: int | None = None) -> Watched:
        result = await session.execute(select(Watched).where(Watched.group_film_id == group_film_id))
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        w = Watched(group_film_id=group_film_id, marked_by_user_id=user_id)
        session.add(w)
        await session.flush()
        return w

    async def is_watched(self, session: AsyncSession, group_film_id: int) -> bool:
        result = await session.execute(select(Watched).where(Watched.group_film_id == group_film_id))
        return result.scalar_one_or_none() is not None
