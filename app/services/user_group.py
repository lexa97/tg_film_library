"""User and group management service."""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import UserRepository, GroupRepository, GroupMemberRepository
from app.db.models import User, Group, GroupMember, RoleEnum


logger = logging.getLogger(__name__)


class UserGroupService:
    """Service for user and group management."""
    
    def __init__(self, session: AsyncSession):
        """Initialize service.
        
        Args:
            session: Database session
        """
        self.session = session
        self.user_repo = UserRepository(session)
        self.group_repo = GroupRepository(session)
        self.member_repo = GroupMemberRepository(session)
    
    async def get_or_create_user(
        self,
        telegram_user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None
    ) -> User:
        """Get existing user or create new one.
        
        Args:
            telegram_user_id: Telegram user ID
            username: Username
            first_name: First name
            last_name: Last name
            phone: Phone number
            
        Returns:
            User instance
        """
        user = await self.user_repo.get_by_telegram_id(telegram_user_id)
        
        if user is None:
            logger.info(f"Creating new user: {telegram_user_id}")
            user = await self.user_repo.create_user(
                telegram_user_id=telegram_user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                phone=phone
            )
        
        return user
    
    async def create_group(self, name: str, admin_user_id: int) -> Group:
        """Create new group with admin.
        
        Args:
            name: Group name
            admin_user_id: Admin user ID (internal DB ID)
            
        Returns:
            Created group
        """
        logger.info(f"Creating group '{name}' with admin {admin_user_id}")
        
        # Create group
        group = await self.group_repo.create_group(
            name=name,
            admin_user_id=admin_user_id
        )
        
        # Add admin as member
        await self.member_repo.add_member(
            group_id=group.id,
            user_id=admin_user_id,
            role=RoleEnum.ADMIN
        )
        
        return group
    
    async def get_user_group(self, user_id: int) -> Optional[GroupMember]:
        """Get user's group (MVP: one group per user).
        
        Args:
            user_id: User ID (internal DB ID)
            
        Returns:
            GroupMember or None if user is not in any group
        """
        memberships = await self.member_repo.get_user_groups(user_id)
        return memberships[0] if memberships else None
    
    async def is_admin(self, user_id: int, group_id: int) -> bool:
        """Check if user is admin of the group.
        
        Args:
            user_id: User ID
            group_id: Group ID
            
        Returns:
            True if user is admin
        """
        membership = await self.member_repo.get_by_user_and_group(user_id, group_id)
        return membership is not None and membership.role == RoleEnum.ADMIN
    
    async def add_member_by_contact(
        self,
        admin_user_id: int,
        contact_telegram_user_id: int
    ) -> tuple[GroupMember, Group]:
        """Add user to admin's group by contact.
        
        Args:
            admin_user_id: Admin's user ID (internal DB ID)
            contact_telegram_user_id: Telegram user ID from contact
            
        Returns:
            Tuple of (created membership, group)
            
        Raises:
            ValueError: If admin has no group or user not found
        """
        # Get admin's group
        admin_membership = await self.get_user_group(admin_user_id)
        if not admin_membership:
            raise ValueError("Admin is not in any group")
        
        group = admin_membership.group
        
        # Check admin rights
        if not await self.is_admin(admin_user_id, group.id):
            raise ValueError("User is not admin of the group")
        
        # Get user by telegram ID
        user = await self.user_repo.get_by_telegram_id(contact_telegram_user_id)
        if not user:
            raise ValueError("User not found. They must start the bot first.")
        
        # Check if already a member
        existing = await self.member_repo.get_by_user_and_group(user.id, group.id)
        if existing:
            raise ValueError("User is already a member of this group")
        
        # Add as member
        logger.info(f"Adding user {user.id} to group {group.id}")
        membership = await self.member_repo.add_member(
            group_id=group.id,
            user_id=user.id,
            role=RoleEnum.MEMBER
        )
        
        return membership, group
    
    async def get_group_members(self, group_id: int) -> list[User]:
        """Get all members of a group.
        
        Args:
            group_id: Group ID
            
        Returns:
            List of users
        """
        memberships = await self.member_repo.get_group_members(group_id)
        return [m.user for m in memberships]
