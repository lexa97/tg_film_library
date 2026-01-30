from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, ContentType
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_group import (
    get_or_create_user,
    get_user_groups,
    get_user_group,
    create_group,
    get_user_by_telegram_id,
    add_member_to_group,
    is_group_admin,
    get_group_member_telegram_ids,
)
from app.states.group import CreateGroupStates

router = Router()


@router.message(Command("newgroup"), F.text)
@router.message(Command("newgroup"))
async def cmd_newgroup(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await get_or_create_user(
        session,
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name,
    )
    await state.set_state(CreateGroupStates.waiting_for_name)
    await message.answer("Введите название группы:")


@router.message(CreateGroupStates.waiting_for_name, F.text)
async def process_group_name(message: Message, state: FSMContext, session: AsyncSession) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название не может быть пустым. Введите название группы:")
        return
    user = await get_or_create_user(
        session,
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name,
    )
    group = await create_group(session, name, user.id)
    await state.clear()
    await message.answer(f"Группа «{group.name}» создана. Добавляйте участников, отправляя боту контакт (Поделиться контактом).")


@router.message(F.contact)
async def on_contact(message: Message, session: AsyncSession) -> None:
    if not message.contact:
        return
    await get_or_create_user(
        session,
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name,
    )
    group = await get_user_group(session, message.from_user.id)
    if not group:
        await message.answer("Сначала создайте группу (команда /newgroup) или вы должны быть в группе.")
        return
    admin = await is_group_admin(session, group.id, message.from_user.id)
    if not admin:
        await message.answer("Добавлять участников может только админ группы.")
        return

    contact = message.contact
    telegram_id = getattr(contact, "user_id", None)
    if telegram_id is None:
        await message.answer(
            "Не удалось получить id пользователя из контакта. "
            "Попросите участника нажать /start у бота, затем отправьте контакт через «Поделиться контактом» из его профиля."
        )
        return

    new_user = await get_user_by_telegram_id(session, telegram_id)
    if not new_user:
        await message.answer(
            "Этот пользователь ещё не нажимал /start у бота. Попросите его сначала запустить бота."
        )
        return

    member = await add_member_to_group(session, group.id, new_user.id)
    if member is None:
        await message.answer("Пользователь уже в группе.")
        return

    await message.answer(f"Пользователь {new_user.first_name or new_user.username or 'ID ' + str(telegram_id)} добавлен в группу «{group.name}».")

    try:
        await message.bot.send_message(
            telegram_id,
            f"Вас добавили в группу «{group.name}». Используйте /list для списка фильмов, "
            "или отправьте название фильма для поиска и добавления."
        )
    except Exception:
        pass
