from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📌 Закладки"), KeyboardButton(text="✅ Задачи")],
            [KeyboardButton(text="📝 Заметки"), KeyboardButton(text="⚙️ Настройки")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_bookmarks_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Все закладки", callback_data="bookmarks_list")],
        [InlineKeyboardButton(text="➕ Добавить", callback_data="bookmarks_add")],
        [InlineKeyboardButton(text="🗑️ Очистить всё", callback_data="bookmarks_clear")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu_main")]
    ])

def get_reminders_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Мои напоминания", callback_data="reminders_list")],
        [InlineKeyboardButton(text="➕ Новое напоминание", callback_data="reminders_add")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu_main")]
    ])

def get_notes_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Все заметки", callback_data="notes_list")],
        [InlineKeyboardButton(text="✏️ Новая заметка", callback_data="notes_add")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu_main")]
    ])

def get_settings_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Язык", callback_data="settings_language")],
        [InlineKeyboardButton(text="🤖 О боте", callback_data="settings_about")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu_main")]
    ])

# 🔑 ИСПРАВЛЕНО: правильная аннотация типа (было: callback_ str)
def get_back_button(callback_ str = "menu_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=callback_data)]
    ])

def get_language_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en")],
        [InlineKeyboardButton(text="🇨🇳 中文", callback_data="lang_zh")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="settings_menu")]
    ])

def get_subscription_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📺 Перейти в канал", url="https://t.me/bot_pro_bot_you")],
        [InlineKeyboardButton(text="🔍 Проверить подписку", callback_data="check_subscription")]
    ])
