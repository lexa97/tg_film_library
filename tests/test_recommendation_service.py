"""Тесты RecommendationService (/relative)."""

from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Film,
    FilmRecommendationCache,
    Group,
    GroupFilm,
    GroupMember,
    RoleEnum,
    User,
    Watched,
)
from app.services.dto import FilmSearchResult
from app.services.recommendation_service import (
    RecommendationService,
    RelativeOutcomeKind,
)


@pytest.mark.asyncio
async def test_relative_no_watched(db_session: AsyncSession):
    user = User(telegram_user_id=1, username="u")
    db_session.add(user)
    await db_session.flush()
    group = Group(name="G", admin_user_id=user.id)
    db_session.add(group)
    await db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=user.id, role=RoleEnum.ADMIN))
    film = Film(
        external_id="1",
        source="tmdb",
        title="A",
        media_type="movie",
    )
    db_session.add(film)
    await db_session.flush()
    db_session.add(
        GroupFilm(group_id=group.id, film_id=film.id, added_by_user_id=user.id)
    )
    await db_session.commit()

    mock = AsyncMock()
    out = await RecommendationService(db_session, mock).build_relative_suggestions(group.id)
    assert out.kind == RelativeOutcomeKind.NO_WATCHED


@pytest.mark.asyncio
async def test_relative_cache_empty(db_session: AsyncSession):
    user = User(telegram_user_id=2, username="u")
    db_session.add(user)
    await db_session.flush()
    group = Group(name="G", admin_user_id=user.id)
    db_session.add(group)
    await db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=user.id, role=RoleEnum.ADMIN))
    film = Film(
        external_id="10",
        source="tmdb",
        title="Watched",
        media_type="movie",
    )
    db_session.add(film)
    await db_session.flush()
    gf = GroupFilm(group_id=group.id, film_id=film.id, added_by_user_id=user.id)
    db_session.add(gf)
    await db_session.flush()
    db_session.add(Watched(group_film_id=gf.id, marked_by_user_id=user.id))
    await db_session.commit()

    mock = AsyncMock()
    out = await RecommendationService(db_session, mock).build_relative_suggestions(group.id)
    assert out.kind == RelativeOutcomeKind.CACHE_EMPTY


@pytest.mark.asyncio
async def test_relative_ok_ranking(db_session: AsyncSession):
    user = User(telegram_user_id=3, username="u")
    db_session.add(user)
    await db_session.flush()
    group = Group(name="G", admin_user_id=user.id)
    db_session.add(group)
    await db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=user.id, role=RoleEnum.ADMIN))

    f1 = Film(external_id="100", source="tmdb", title="Src1", media_type="movie")
    f2 = Film(external_id="101", source="tmdb", title="Src2", media_type="movie")
    db_session.add_all([f1, f2])
    await db_session.flush()

    gf1 = GroupFilm(group_id=group.id, film_id=f1.id, added_by_user_id=user.id)
    gf2 = GroupFilm(group_id=group.id, film_id=f2.id, added_by_user_id=user.id)
    db_session.add_all([gf1, gf2])
    await db_session.flush()
    db_session.add(Watched(group_film_id=gf1.id, marked_by_user_id=user.id))
    db_session.add(Watched(group_film_id=gf2.id, marked_by_user_id=user.id))

    # 999 встречается дважды — должен быть первым
    db_session.add(
        FilmRecommendationCache(
            source_film_id=f1.id,
            recommended_external_id="999",
            recommended_media_type="movie",
        )
    )
    db_session.add(
        FilmRecommendationCache(
            source_film_id=f2.id,
            recommended_external_id="999",
            recommended_media_type="movie",
        )
    )
    db_session.add(
        FilmRecommendationCache(
            source_film_id=f1.id,
            recommended_external_id="888",
            recommended_media_type="movie",
        )
    )
    await db_session.commit()

    async def fake_details(ext_id: str, media_type: str):
        return FilmSearchResult(
            external_id=ext_id,
            source="tmdb",
            title=f"T{ext_id}",
            year=2020,
            description="d",
            poster_url=None,
            media_type=media_type,
        )

    mock = AsyncMock()
    mock.get_details = AsyncMock(side_effect=fake_details)

    out = await RecommendationService(db_session, mock).build_relative_suggestions(group.id, limit=5)
    assert out.kind == RelativeOutcomeKind.OK
    assert len(out.results) == 2
    assert out.results[0].external_id == "999"
    assert out.results[1].external_id == "888"


@pytest.mark.asyncio
async def test_relative_excludes_already_in_group(db_session: AsyncSession):
    user = User(telegram_user_id=4, username="u")
    db_session.add(user)
    await db_session.flush()
    group = Group(name="G", admin_user_id=user.id)
    db_session.add(group)
    await db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=user.id, role=RoleEnum.ADMIN))

    watched = Film(external_id="200", source="tmdb", title="W", media_type="movie")
    already = Film(external_id="300", source="tmdb", title="In list", media_type="movie")
    db_session.add_all([watched, already])
    await db_session.flush()

    gf_w = GroupFilm(group_id=group.id, film_id=watched.id, added_by_user_id=user.id)
    gf_a = GroupFilm(group_id=group.id, film_id=already.id, added_by_user_id=user.id)
    db_session.add_all([gf_w, gf_a])
    await db_session.flush()
    db_session.add(Watched(group_film_id=gf_w.id, marked_by_user_id=user.id))

    db_session.add(
        FilmRecommendationCache(
            source_film_id=watched.id,
            recommended_external_id="300",
            recommended_media_type="movie",
        )
    )
    await db_session.commit()

    mock = AsyncMock()
    out = await RecommendationService(db_session, mock).build_relative_suggestions(group.id)
    assert out.kind == RelativeOutcomeKind.NO_CANDIDATES
    mock.get_details.assert_not_called()
