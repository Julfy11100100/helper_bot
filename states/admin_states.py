from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    waiting_for_user_input = State()
    waiting_for_message = State()
    waiting_for_user_delete = State()
    confirming_broadcast = State()