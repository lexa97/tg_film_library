"""Group management handlers."""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_group import UserGroupService
from app.states.group import CreateGroupStates
from app.keyboards.inline import build_main_menu_keyboard
from app.keyboards.reply import build_main_reply_keyboard


logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "create_group")
async def start_group_creation(callback: CallbackQuery, state: FSMContext):
    """Start group creation flow.
    
    Args:
        callback: Callback query
        state: FSM state
    """
    await callback.message.edit_text(
        "➕ <b>Создание группы</b>\n\n"
        "Введите название группы:",
        parse_mode="HTML"
    )
    
    await state.set_state(CreateGroupStates.waiting_for_name)
    await callback.answer()


@router.message(CreateGroupStates.waiting_for_name)
async def process_group_name(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Process group name and create group.
    
    Args:
        message: Telegram message
        state: FSM state
        session: Database session
    """
    group_name = message.text.strip()
    
    if not group_name or len(group_name) > 255:
        await message.answer(
            "❌ Название группы должно быть от 1 до 255 символов. Попробуйте ещё раз:"
        )
        return
    
    # Get or create user
    user = message.from_user
    service = UserGroupService(session)
    db_user = await service.get_or_create_user(
        telegram_user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Check if user already in a group
    existing_membership = await service.get_user_group(db_user.id)
    if existing_membership:
        await message.answer(
            "❌ Вы уже состоите в группе. В текущей версии можно быть только в одной группе."
        )
        await state.clear()
        return
    
    # Create group
    try:
        group = await service.create_group(
            name=group_name,
            admin_user_id=db_user.id
        )
        
        # Устанавливаем Reply-клавиатуру и отправляем сообщение
        await message.answer(
            f"✅ Группа <b>«{group.name}»</b> успешно создана!\n\n"
            f"Вы можете добавлять участников, отправляя боту их контакты "
            f"(Поделиться контактом из профиля пользователя).\n\n"
            f"Начните искать фильмы, просто отправив название!",
            parse_mode="HTML",
            reply_markup=build_main_reply_keyboard(has_group=True)
        )
        
        # Отправляем inline-меню
        await message.answer(
            "📱 <b>Меню:</b>",
            parse_mode="HTML",
            reply_markup=build_main_menu_keyboard(has_group=True)
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error creating group: {e}")
        await message.answer(
            "❌ Произошла ошибка при создании группы. Попробуйте позже."
        )
        await state.clear()


@router.message(F.text == "➕ Создать группу")
async def reply_create_group(message: Message, state: FSMContext, session: AsyncSession):
    """Handle '➕ Создать группу' reply button.
    
    Args:
        message: Telegram message
        state: FSM state
        session: Database session
    """
    user = message.from_user
    
    # Проверяем что пользователь не состоит в группе
    service = UserGroupService(session)
    db_user = await service.get_or_create_user(
        telegram_user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    membership = await service.get_user_group(db_user.id)
    if membership:
        await message.answer(
            f"⚠️ Вы уже состоите в группе «{membership.group.name}».\n\n"
            f"В текущей версии можно состоять только в одной группе."
        )
        return
    
    # Начинаем процесс создания группы
    await message.answer(
        "➕ <b>Создание группы</b>\n\n"
        "Введите название группы:",
        parse_mode="HTML"
    )
    
    await state.set_state(CreateGroupStates.waiting_for_name)
