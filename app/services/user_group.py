from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Group, GroupMember, User


async def get_or_create_user(
    session: AsyncSession,
    telegram_user_id: int,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> User:
    result = await session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
    user = result.scalar_one_or_none()
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


async def get_user_groups(session: AsyncSession, telegram_user_id: int) -> list[Group]:
    result = await session.execute(
        select(Group)
        .join(GroupMember, Group.id == GroupMember.group_id)
        .join(User, GroupMember.user_id == User.id)
        .where(User.telegram_user_id == telegram_user_id)
    )
    return list(result.scalars().all())


async def get_user_group(session: AsyncSession, telegram_user_id: int) -> Group | None:
    groups = await get_user_groups(session, telegram_user_id)
    return groups[0] if groups else None


async def create_group(session: AsyncSession, name: str, admin_user_id: int) -> Group:
    group = Group(name=name.strip(), admin_user_id=admin_user_id)
    session.add(group)
    await session.flush()
    member = GroupMember(group_id=group.id, user_id=admin_user_id, role="admin")
    session.add(member)
    await session.flush()
    return group


async def get_user_by_telegram_id(session: AsyncSession, telegram_user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
    return result.scalar_one_or_none()


async def add_member_to_group(session: AsyncSession, group_id: int, user_id: int) -> GroupMember | None:
    result = await session.execute(
        select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
    )
    if result.scalar_one_or_none():
        return None
    member = GroupMember(group_id=group_id, user_id=user_id, role="member")
    session.add(member)
    await session.flush()
    return member


async def get_group_member_telegram_ids(session: AsyncSession, group_id: int) -> list[int]:
    result = await session.execute(
        select(User.telegram_user_id).join(GroupMember, User.id == GroupMember.user_id).where(GroupMember.group_id == group_id)
    )
    return list(result.scalars().all())


async def is_group_admin(session: AsyncSession, group_id: int, telegram_user_id: int) -> bool:
    result = await session.execute(
        select(GroupMember)
        .join(User, GroupMember.user_id == User.id)
        .where(GroupMember.group_id == group_id, User.telegram_user_id == telegram_user_id)
    )
    m = result.scalar_one_or_none()
    return m is not None and m.role == "admin"
