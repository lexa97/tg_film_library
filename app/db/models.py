"""SQLAlchemy database models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class RoleEnum(enum.Enum):
    """Group member role."""
    ADMIN = "admin"
    MEMBER = "member"


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    admin_groups: Mapped[list["Group"]] = relationship(
        "Group", 
        back_populates="admin",
        foreign_keys="Group.admin_user_id"
    )
    group_memberships: Mapped[list["GroupMember"]] = relationship(
        "GroupMember", 
        back_populates="user"
    )
    added_films: Mapped[list["GroupFilm"]] = relationship(
        "GroupFilm",
        back_populates="added_by_user"
    )


class Group(Base):
    """Group model."""
    
    __tablename__ = "groups"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    admin_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    admin: Mapped["User"] = relationship(
        "User",
        back_populates="admin_groups",
        foreign_keys=[admin_user_id]
    )
    members: Mapped[list["GroupMember"]] = relationship(
        "GroupMember",
        back_populates="group"
    )
    films: Mapped[list["GroupFilm"]] = relationship(
        "GroupFilm",
        back_populates="group"
    )


class GroupMember(Base):
    """Group member association."""
    
    __tablename__ = "group_members"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum))
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="group_memberships")


class Film(Base):
    """Film/series model."""
    
    __tablename__ = "films"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(50), index=True)
    source: Mapped[str] = mapped_column(String(50))  # 'tmdb'
    title: Mapped[str] = mapped_column(String(500))
    title_original: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    year: Mapped[Optional[int]] = mapped_column(nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    poster_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    group_associations: Mapped[list["GroupFilm"]] = relationship(
        "GroupFilm",
        back_populates="film"
    )


class GroupFilm(Base):
    """Association between group and film."""
    
    __tablename__ = "group_films"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    film_id: Mapped[int] = mapped_column(ForeignKey("films.id"), index=True)
    added_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="films")
    film: Mapped["Film"] = relationship("Film", back_populates="group_associations")
    added_by_user: Mapped["User"] = relationship("User", back_populates="added_films")
    watched: Mapped[Optional["Watched"]] = relationship(
        "Watched",
        back_populates="group_film",
        uselist=False
    )


class Watched(Base):
    """Watched status for a film in a group."""
    
    __tablename__ = "watched"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    group_film_id: Mapped[int] = mapped_column(
        ForeignKey("group_films.id"), 
        unique=True,
        index=True
    )
    watched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    marked_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # Relationships
    group_film: Mapped["GroupFilm"] = relationship("GroupFilm", back_populates="watched")
    marked_by_user: Mapped["User"] = relationship("User")
