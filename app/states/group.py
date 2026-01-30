from aiogram.fsm.state import State, StatesGroup


class CreateGroupStates(StatesGroup):
    waiting_for_name = State()
