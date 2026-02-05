from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Постоянная клавиатура внизу чата (как в заметках Viber)
    Две кнопки в один ряд для минимализма
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🚀 Старт"),
                KeyboardButton(text="🔍 Поиск")
            ]
        ],
        resize_keyboard=True,      # Адаптивный размер под устройство
        one_time_keyboard=False,   # Клавиатура всегда видна (не скрывается после нажатия)
        input_field_placeholder="Напишите заметку или нажмите 🔍 Поиск..."  # Подсказка в поле ввода
    )

def get_search_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура во время поиска — только отмена
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отменить поиск")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Введите слово для поиска..."
    )
