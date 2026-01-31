"""Tests for UserGroupService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_group import UserGroupService
from app.db.models import RoleEnum


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    """Test user creation."""
    service = UserGroupService(db_session)
    
    user = await service.get_or_create_user(
        telegram_user_id=12345,
        username="testuser",
        first_name="Test",
        last_name="User"
    )
    
    assert user.telegram_user_id == 12345
    assert user.username == "testuser"
    assert user.first_name == "Test"
    assert user.last_name == "User"


@pytest.mark.asyncio
async def test_create_group(db_session: AsyncSession):
    """Test group creation."""
    service = UserGroupService(db_session)
    
    # Create user first
    user = await service.get_or_create_user(
        telegram_user_id=12345,
        username="admin",
        first_name="Admin"
    )
    
    # Create group
    group = await service.create_group(
        name="Test Group",
        admin_user_id=user.id
    )
    
    assert group.name == "Test Group"
    assert group.admin_user_id == user.id


@pytest.mark.asyncio
async def test_add_member_by_contact(db_session: AsyncSession):
    """Test adding member by contact."""
    service = UserGroupService(db_session)
    
    # Create admin and group
    admin = await service.get_or_create_user(
        telegram_user_id=11111,
        username="admin",
        first_name="Admin"
    )
    
    group = await service.create_group(
        name="Test Group",
        admin_user_id=admin.id
    )
    
    # Create member
    member_user = await service.get_or_create_user(
        telegram_user_id=22222,
        username="member",
        first_name="Member"
    )
    
    # Add member to group
    membership, returned_group = await service.add_member_by_contact(
        admin_user_id=admin.id,
        contact_telegram_user_id=22222
    )
    
    assert membership.user_id == member_user.id
    assert membership.group_id == group.id
    assert membership.role == RoleEnum.MEMBER
    assert returned_group.id == group.id


@pytest.mark.asyncio
async def test_get_user_group(db_session: AsyncSession):
    """Test getting user's group."""
    service = UserGroupService(db_session)
    
    # Create user and group
    user = await service.get_or_create_user(
        telegram_user_id=12345,
        username="user",
        first_name="User"
    )
    
    group = await service.create_group(
        name="Test Group",
        admin_user_id=user.id
    )
    
    # Get user's group
    membership = await service.get_user_group(user.id)
    
    assert membership is not None
    assert membership.group_id == group.id
    assert membership.role == RoleEnum.ADMIN


@pytest.mark.asyncio
async def test_is_admin(db_session: AsyncSession):
    """Test admin check."""
    service = UserGroupService(db_session)
    
    # Create admin and group
    admin = await service.get_or_create_user(
        telegram_user_id=11111,
        username="admin",
        first_name="Admin"
    )
    
    group = await service.create_group(
        name="Test Group",
        admin_user_id=admin.id
    )
    
    # Check admin
    is_admin = await service.is_admin(admin.id, group.id)
    assert is_admin is True
    
    # Create and add member
    member = await service.get_or_create_user(
        telegram_user_id=22222,
        username="member",
        first_name="Member"
    )
    
    await service.add_member_by_contact(
        admin_user_id=admin.id,
        contact_telegram_user_id=22222
    )
    
    # Check member is not admin
    is_member_admin = await service.is_admin(member.id, group.id)
    assert is_member_admin is False
