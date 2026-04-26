from aiogram.fsm.state import State, StatesGroup


class CheckoutState(StatesGroup):
    """Шаги оформления заказа.

    Каждое состояние — это техническая отметка 'на каком шаге диалог'.
    Хендлеры фильтруются по этим состояниям.
    """

    waiting_address = State()
    waiting_delivery = State()
    waiting_phone = State()
    waiting_payment = State()
    waiting_comment = State()
    waiting_promo = State()
    waiting_confirmation = State()
