from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Film, GroupFilm, Watched


async def find_film_by_external(session: AsyncSession, external_id: str, source: str) -> Film | None:
    result = await session.execute(
        select(Film).where(Film.external_id == external_id, Film.source == source)
    )
    return result.scalar_one_or_none()


async def create_film(session: AsyncSession, film_data: dict) -> Film:
    film = Film(**film_data)
    session.add(film)
    await session.flush()
    return film


async def add_film_to_group(
    session: AsyncSession,
    group_id: int,
    film_id: int,
    added_by_user_id: int,
) -> GroupFilm:
    gf = GroupFilm(group_id=group_id, film_id=film_id, added_by_user_id=added_by_user_id)
    session.add(gf)
    await session.flush()
    return gf


async def get_group_films(
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


async def get_group_film_by_id(session: AsyncSession, group_film_id: int, group_id: int) -> tuple[GroupFilm, Film] | None:
    result = await session.execute(
        select(GroupFilm, Film)
        .join(Film, GroupFilm.film_id == Film.id)
        .where(GroupFilm.id == group_film_id, GroupFilm.group_id == group_id)
    )
    row = result.one_or_none()
    return row


async def mark_as_watched(session: AsyncSession, group_film_id: int, user_id: int | None = None) -> Watched:
    result = await session.execute(select(Watched).where(Watched.group_film_id == group_film_id))
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    w = Watched(group_film_id=group_film_id, marked_by_user_id=user_id)
    session.add(w)
    await session.flush()
    return w


async def is_watched(session: AsyncSession, group_film_id: int) -> bool:
    result = await session.execute(select(Watched).where(Watched.group_film_id == group_film_id))
    return result.scalar_one_or_none() is not None
