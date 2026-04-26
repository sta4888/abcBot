from aiogram.fsm.state import State, StatesGroup


class AdminCategoryFSM(StatesGroup):
    waiting_name = State()


class AdminCategoryRenameFSM(StatesGroup):
    waiting_name = State()


class AdminProductFSM(StatesGroup):
    waiting_name = State()
    waiting_description = State()
    waiting_price = State()
    waiting_stock = State()
    waiting_photo = State()
