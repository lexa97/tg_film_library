"""Group member repository."""

from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GroupMember, RoleEnum
from app.db.repositories.base import BaseRepository


class GroupMemberRepository(BaseRepository[GroupMember]):
    """Repository for GroupMember model."""
    
    def __init__(self, session: AsyncSession):
        """Initialize group member repository.
        
        Args:
            session: Database session
        """
        super().__init__(GroupMember, session)
    
    async def get_by_user_and_group(
        self, 
        user_id: int, 
        group_id: int
    ) -> Optional[GroupMember]:
        """Get group member by user and group.
        
        Args:
            user_id: User ID
            group_id: Group ID
            
        Returns:
            GroupMember or None if not found
        """
        result = await self.session.execute(
            select(GroupMember)
            .options(selectinload(GroupMember.group), selectinload(GroupMember.user))
            .where(
                and_(
                    GroupMember.user_id == user_id,
                    GroupMember.group_id == group_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_groups(self, user_id: int) -> list[GroupMember]:
        """Get all groups where user is a member.
        
        Args:
            user_id: User ID
            
        Returns:
            List of group memberships
        """
        result = await self.session.execute(
            select(GroupMember)
            .options(selectinload(GroupMember.group), selectinload(GroupMember.user))
            .where(GroupMember.user_id == user_id)
        )
        return list(result.scalars().all())
    
    async def get_group_members(self, group_id: int) -> list[GroupMember]:
        """Get all members of a group.
        
        Args:
            group_id: Group ID
            
        Returns:
            List of group members
        """
        result = await self.session.execute(
            select(GroupMember)
            .options(selectinload(GroupMember.group), selectinload(GroupMember.user))
            .where(GroupMember.group_id == group_id)
        )
        return list(result.scalars().all())
    
    async def add_member(
        self,
        group_id: int,
        user_id: int,
        role: RoleEnum = RoleEnum.MEMBER
    ) -> GroupMember:
        """Add member to group.
        
        Args:
            group_id: Group ID
            user_id: User ID
            role: Member role
            
        Returns:
            Created group member
        """
        membership = await self.create(
            group_id=group_id,
            user_id=user_id,
            role=role
        )
        
        # Перезагружаем со связанными объектами
        result = await self.session.execute(
            select(GroupMember)
            .options(selectinload(GroupMember.group), selectinload(GroupMember.user))
            .where(GroupMember.id == membership.id)
        )
        return result.scalar_one()
