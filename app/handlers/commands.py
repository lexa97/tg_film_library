"""Basic command handlers."""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_group import UserGroupService
from app.services.recommendation_service import (
    RecommendationService,
    RelativeOutcomeKind,
)
from app.services.tmdb import TMDBFilmSearch
from app.handlers.film_cards import send_film_search_result_cards
from app.keyboards.inline import build_main_menu_keyboard


logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession):
    """Handle /start command.
    
    Args:
        message: Telegram message
        session: Database session
    """
    user = message.from_user
    
    # Get or create user
    service = UserGroupService(session)
    db_user = await service.get_or_create_user(
        telegram_user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Check if user is in a group
    membership = await service.get_user_group(db_user.id)
    
    if membership:
        # User is in a group
        group = membership.group
        text = (
            f"👋 Привет, {user.first_name}!\n\n"
            f"Вы участник группы: <b>{group.name}</b>\n\n"
            f"Отправьте название фильма для поиска или используйте кнопки меню."
        )
        inline_keyboard = build_main_menu_keyboard(has_group=True)
    else:
        # User is not in any group
        text = (
            f"👋 Привет, {user.first_name}!\n\n"
            f"Вас ещё нет ни в одной группе.\n\n"
            f"Вы можете:\n"
            f"• Создать свою группу с помощью кнопки ниже\n"
            f"• Попросить администратора группы добавить вас, отправив ему ваш контакт "
            f"(Настройки → Поделиться контактом)"
        )
        inline_keyboard = build_main_menu_keyboard(has_group=False)
    
    await message.answer(text, parse_mode="HTML", reply_markup=inline_keyboard)


@router.message(Command("relative"))
async def cmd_relative(message: Message, session: AsyncSession):
    """Подборка по кэшу TMDB recommendations и просмотренным в группе."""
    user = message.from_user
    service = UserGroupService(session)
    db_user = await service.get_or_create_user(
        telegram_user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    membership = await service.get_user_group(db_user.id)
    if not membership:
        await message.answer(
            "❌ Вы не состоите ни в одной группе.\n"
            "Создайте группу или попросите администратора добавить вас."
        )
        return

    rec = RecommendationService(session, TMDBFilmSearch())
    outcome = await rec.build_relative_suggestions(membership.group.id)

    if outcome.kind == RelativeOutcomeKind.NO_WATCHED:
        await message.answer(
            "📽 Сначала отметьте хотя бы один фильм как просмотренный — "
            "тогда можно будет предложить похожее."
        )
        return
    if outcome.kind == RelativeOutcomeKind.CACHE_EMPTY:
        await message.answer(
            "⏳ Кэш рекомендаций ещё не готов. Обычно он заполняется в фоне в течение минуты "
            "после старта бота; если прошло долго — проверьте логи и доступ к TMDB."
        )
        return
    if outcome.kind == RelativeOutcomeKind.NO_CANDIDATES:
        await message.answer(
            "Пока нечего предложить: все варианты из кэша уже в списке группы или не удалось загрузить карточки."
        )
        return

    await send_film_search_result_cards(
        message,
        outcome.results,
        intro_line=f"🎯 Подборка по просмотренным: {len(outcome.results)}\n",
    )


@router.message(Command("list"))
async def cmd_list(message: Message, session: AsyncSession):
    """Handle /list command.
    
    Args:
        message: Telegram message
        session: Database session
    """
    from app.handlers.list import show_film_list
    await show_film_list(message, session, page=0)
