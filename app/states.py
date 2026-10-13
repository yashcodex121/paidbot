from aiogram.fsm.state import State, StatesGroup


class PayStates(StatesGroup):
    waiting_screenshot = State()


class BroadcastStates(StatesGroup):
    waiting_message = State()
    confirming = State()


class TopUpStates(StatesGroup):
    choosing_amount = State()
    waiting_screenshot = State()
