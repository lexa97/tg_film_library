from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.inline import btn_list
from app.services.user_group import get_or_create_user, get_user_groups

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    user = await get_or_create_user(
        session,
        telegram_user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    groups = await get_user_groups(session, message.from_user.id)
    if not groups:
        await message.answer(
            "Вас ещё нет ни в одной группе.\n\n"
            "Сначала нажмите /start у бота, затем попросите админа добавить вас, "
            "отправив ему ваш контакт для пересылки боту."
        )
        return
    group_names = ", ".join(g.name for g in groups)
    await message.answer(
        f"Вы в группе: {group_names}.\n\n"
        "Команды:\n"
        "/list — список фильмов группы\n"
        "Отправьте название фильма или сериала — поиск и добавление в список\n\n"
        "Если вы админ: создайте группу через меню или добавьте участников, отправив контакт.",
        reply_markup=btn_list(),
    )
