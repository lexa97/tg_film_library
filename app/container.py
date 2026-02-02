"""
Контейнер репозиториев и сервисов. Инициализация при старте приложения.
Хендлеры получают сервисы через middleware (data).
"""
from app.db.repositories import (
    FilmRepository,
    GroupFilmRepository,
    GroupMemberRepository,
    GroupRepository,
    UserRepository,
    WatchedRepository,
)
from app.services.group_film_service import GroupFilmService
from app.services.tmdb_provider import TMDBFilmSearch
from app.services.user_group_service import UserGroupService

_user_repo: UserRepository | None = None
_group_repo: GroupRepository | None = None
_group_member_repo: GroupMemberRepository | None = None
_film_repo: FilmRepository | None = None
_group_film_repo: GroupFilmRepository | None = None
_watched_repo: WatchedRepository | None = None
_film_search: TMDBFilmSearch | None = None
_user_group_service: UserGroupService | None = None
_group_film_service: GroupFilmService | None = None


def init_container() -> None:
    """Создать репозитории и сервисы (один раз при старте)."""
    global _user_repo, _group_repo, _group_member_repo, _film_repo, _group_film_repo, _watched_repo
    global _film_search, _user_group_service, _group_film_service
    _user_repo = UserRepository()
    _group_repo = GroupRepository()
    _group_member_repo = GroupMemberRepository()
    _film_repo = FilmRepository()
    _group_film_repo = GroupFilmRepository()
    _watched_repo = WatchedRepository()
    _film_search = TMDBFilmSearch()
    _user_group_service = UserGroupService(_user_repo, _group_repo, _group_member_repo)
    _group_film_service = GroupFilmService(
        _user_repo,
        _group_repo,
        _film_repo,
        _group_film_repo,
        _watched_repo,
        _group_member_repo,
        _film_search,
    )


def get_user_group_service() -> UserGroupService:
    if _user_group_service is None:
        raise RuntimeError("Container not initialized. Call init_container() first.")
    return _user_group_service


def get_group_film_service() -> GroupFilmService:
    if _group_film_service is None:
        raise RuntimeError("Container not initialized. Call init_container() first.")
    return _group_film_service


def get_film_search() -> TMDBFilmSearch:
    if _film_search is None:
        raise RuntimeError("Container not initialized. Call init_container() first.")
    return _film_search
