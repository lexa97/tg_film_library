"""Group film repository."""

from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import GroupFilm, Film, Watched
from app.db.repositories.base import BaseRepository


class GroupFilmRepository(BaseRepository[GroupFilm]):
    """Repository for GroupFilm model."""
    
    def __init__(self, session: AsyncSession):
        """Initialize group film repository.
        
        Args:
            session: Database session
        """
        super().__init__(GroupFilm, session)
    
    async def get_by_id(self, id: int) -> Optional[GroupFilm]:
        """Get group film by ID with eager loading of relations.
        
        Args:
            id: GroupFilm ID
            
        Returns:
            GroupFilm with film and watched loaded, or None if not found
        """
        result = await self.session.execute(
            select(GroupFilm)
            .where(GroupFilm.id == id)
            .options(
                selectinload(GroupFilm.film),
                selectinload(GroupFilm.watched)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_group_films(
        self,
        group_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> list[GroupFilm]:
        """Get films for a group with pagination.
        
        Args:
            group_id: Group ID
            limit: Maximum number of films to return
            offset: Number of films to skip
            
        Returns:
            List of group films with relations loaded
        """
        result = await self.session.execute(
            select(GroupFilm)
            .outerjoin(Watched, GroupFilm.id == Watched.group_film_id)
            .join(Film, GroupFilm.film_id == Film.id)
            .where(GroupFilm.group_id == group_id)
            .options(
                selectinload(GroupFilm.film),
                selectinload(GroupFilm.watched)
            )
            .order_by(
                Watched.id.asc().nulls_first(),  # непросмотренные первыми
                Film.title.asc()
            )
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def count_group_films(self, group_id: int) -> int:
        """Count total films in a group.
        
        Args:
            group_id: Group ID
            
        Returns:
            Total number of films
        """
        result = await self.session.execute(
            select(GroupFilm).where(GroupFilm.group_id == group_id)
        )
        return len(list(result.scalars().all()))
    
    async def get_by_film_and_group(
        self,
        film_id: int,
        group_id: int
    ) -> Optional[GroupFilm]:
        """Get group film by film ID and group ID.
        
        Args:
            film_id: Film ID
            group_id: Group ID
            
        Returns:
            GroupFilm or None if not found
        """
        result = await self.session.execute(
            select(GroupFilm)
            .where(
                and_(
                    GroupFilm.film_id == film_id,
                    GroupFilm.group_id == group_id
                )
            )
            .options(
                selectinload(GroupFilm.film),
                selectinload(GroupFilm.watched)
            )
        )
        return result.scalar_one_or_none()
    
    async def add_film_to_group(
        self,
        group_id: int,
        film_id: int,
        added_by_user_id: int
    ) -> GroupFilm:
        """Add film to group.
        
        Args:
            group_id: Group ID
            film_id: Film ID
            added_by_user_id: User ID who added the film
            
        Returns:
            Created group film with relations loaded
        """
        group_film = await self.create(
            group_id=group_id,
            film_id=film_id,
            added_by_user_id=added_by_user_id
        )
        
        # Перезагружаем со связанными объектами
        result = await self.session.execute(
            select(GroupFilm)
            .where(GroupFilm.id == group_film.id)
            .options(
                selectinload(GroupFilm.film),
                selectinload(GroupFilm.watched)
            )
        )
        return result.scalar_one()
    
    async def distinct_film_ids_in_use(self) -> list[int]:
        """Уникальные film_id, которые есть хотя бы в одной группе (для фона кэша рекомендаций)."""
        result = await self.session.execute(select(GroupFilm.film_id).distinct())
        return [int(x[0]) for x in result.all()]

    async def list_group_external_keys(self, group_id: int) -> set[tuple[str, str]]:
        """Пары (external_id, media_type) фильмов уже в списке группы."""
        result = await self.session.execute(
            select(Film.external_id, Film.media_type)
            .join(GroupFilm, GroupFilm.film_id == Film.id)
            .where(GroupFilm.group_id == group_id)
        )
        return {(str(r[0]), str(r[1])) for r in result.all()}

    async def watched_film_ids_for_group(self, group_id: int) -> list[int]:
        """film_id просмотренных в группе title."""
        result = await self.session.execute(
            select(GroupFilm.film_id)
            .join(Watched, Watched.group_film_id == GroupFilm.id)
            .where(GroupFilm.group_id == group_id)
        )
        return [int(x[0]) for x in result.all()]

    async def watched_film_media_types(self, group_id: int) -> list[str]:
        """media_type просмотренных фильмов (для фильтра movie/tv в подборке)."""
        result = await self.session.execute(
            select(Film.media_type)
            .join(GroupFilm, GroupFilm.film_id == Film.id)
            .join(Watched, Watched.group_film_id == GroupFilm.id)
            .where(GroupFilm.group_id == group_id)
        )
        return [str(x[0] or "movie") for x in result.all()]

    async def search_in_group(
        self,
        group_id: int,
        query: str
    ) -> list[GroupFilm]:
        """Search films in group by title.
        
        Args:
            group_id: Group ID
            query: Search query
            
        Returns:
            List of matching group films
        """
        result = await self.session.execute(
            select(GroupFilm)
            .join(Film)
            .where(
                and_(
                    GroupFilm.group_id == group_id,
                    Film.title.ilike(f"%{query}%")
                )
            )
            .options(
                selectinload(GroupFilm.film),
                selectinload(GroupFilm.watched)
            )
        )
        return list(result.scalars().all())
