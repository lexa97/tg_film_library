"""
Сервис пользователей и групп: сценарии /start, создание группы, добавление по контакту.
Вся бизнес-логика и уведомления — здесь.
"""
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Group, User
from app.db.repositories import GroupMemberRepository, GroupRepository, UserRepository
from app.schemas import AddMemberResult


class UserGroupService:
    def __init__(
        self,
        user_repo: UserRepository,
        group_repo: GroupRepository,
        group_member_repo: GroupMemberRepository,
    ) -> None:
        self._user = user_repo
        self._group = group_repo
        self._member = group_member_repo

    async def get_or_create_user(
        self,
        session: AsyncSession,
        telegram_user_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        return await self._user.get_or_create(
            session, telegram_user_id, username=username, first_name=first_name, last_name=last_name
        )

    async def get_user_group(self, session: AsyncSession, telegram_user_id: int) -> Group | None:
        groups = await self._member.get_user_groups(session, telegram_user_id)
        return groups[0] if groups else None

    async def get_user_groups(self, session: AsyncSession, telegram_user_id: int) -> list[Group]:
        return await self._member.get_user_groups(session, telegram_user_id)

    async def create_group(
        self, session: AsyncSession, name: str, admin_telegram_id: int
    ) -> Group:
        user = await self._user.get_or_create(session, admin_telegram_id)
        group = await self._group.create(session, name, user.id)
        await self._member.add_member(session, group.id, user.id, role="admin")
        return group

    async def add_member_by_contact(
        self,
        session: AsyncSession,
        admin_telegram_id: int,
        contact_user_id: int | None,
        bot: Bot | None = None,
    ) -> AddMemberResult:
        """Добавить участника по контакту (contact.user_id). Проверки и уведомления внутри."""
        if contact_user_id is None:
            return AddMemberResult(
                success=False,
                error="Не удалось получить id пользователя из контакта. "
                "Попросите участника нажать /start у бота, затем отправьте контакт через «Поделиться контактом» из его профиля.",
            )
        group = await self.get_user_group(session, admin_telegram_id)
        if not group:
            return AddMemberResult(
                success=False,
                error="Сначала создайте группу (команда /newgroup) или вы должны быть в группе.",
            )
        is_admin = await self._member.is_admin(session, group.id, admin_telegram_id)
        if not is_admin:
            return AddMemberResult(success=False, error="Добавлять участников может только админ группы.")
        new_user = await self._user.get_by_telegram_id(session, contact_user_id)
        if not new_user:
            return AddMemberResult(
                success=False,
                error="Этот пользователь ещё не нажимал /start у бота. Попросите его сначала запустить бота.",
            )
        member = await self._member.add_member(session, group.id, new_user.id, role="member")
        if member is None:
            return AddMemberResult(success=False, error="Пользователь уже в группе.")
        display_name = new_user.first_name or new_user.username or f"ID {contact_user_id}"
        if bot:
            try:
                await bot.send_message(
                    contact_user_id,
                    f"Вас добавили в группу «{group.name}». Используйте /list для списка фильмов, "
                    "или отправьте название фильма для поиска и добавления.",
                )
            except Exception:
                pass
        return AddMemberResult(
            success=True,
            group_name=group.name,
            new_member_display_name=display_name,
        )
