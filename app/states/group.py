"""FSM states for group operations."""

from aiogram.fsm.state import State, StatesGroup


class CreateGroupStates(StatesGroup):
    """States for group creation."""
    
    waiting_for_name = State()
