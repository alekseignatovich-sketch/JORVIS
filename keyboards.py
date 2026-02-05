from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard() -> InlineKeyboardMarkup:
    """
    Основная клавиатура с двумя кнопками как в заметках Viber:
    • 🚀 Старт — краткая инструкция
    • 🔍 Поиск — поиск по тексту заметок
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Старт", callback_data="start_menu")],
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="search")]
    ])

def get_search_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура отмены поиска"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_search")]
    ])
