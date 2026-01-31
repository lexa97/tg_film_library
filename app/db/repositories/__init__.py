"""Database repositories."""

from app.db.repositories.user import UserRepository
from app.db.repositories.group import GroupRepository
from app.db.repositories.group_member import GroupMemberRepository
from app.db.repositories.film import FilmRepository
from app.db.repositories.group_film import GroupFilmRepository
from app.db.repositories.watched import WatchedRepository

__all__ = [
    "UserRepository",
    "GroupRepository",
    "GroupMemberRepository",
    "FilmRepository",
    "GroupFilmRepository",
    "WatchedRepository",
]
