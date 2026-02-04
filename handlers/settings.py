from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards import get_settings_menu, get_language_menu, get_back_button

router = Router()

@router.callback_query(F.data == "settings_menu")
async def settings_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>\n\n"
        "Настройте бота под себя:",
        reply_markup=get_settings_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "settings_language")
async def language_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🌐 <b>Выберите язык</b>\n\n"
        "Бот поддерживает несколько языков:",
        reply_markup=get_language_menu()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("lang_"))
async def set_language(callback: CallbackQuery):
    lang_code = callback.data.split("_")[1]
    
    languages = {
        "ru": "🇷🇺 Русский",
        "en": "🇺🇸 English",
        "zh": "🇨🇳 中文"
    }
    
    # TODO: Сохранить выбор языка в БД на следующем этапе
    
    await callback.message.edit_text(
        f"✅ Язык изменён на {languages.get(lang_code, lang_code)}",
        reply_markup=get_back_button("settings_menu")
    )
    await callback.answer()

@router.callback_query(F.data == "settings_about")
async def about_bot(callback: CallbackQuery):
    await callback.message.edit_text(
        "🤖 <b>JARVIS — Бот-ассистент</b>\n\n"
        "Версия: 1.0 (MVP)\n"
        "Создан для помощи в повседневных задачах.\n\n"
        "<b>Функции:</b>\n"
        "• 📌 Закладки — сохраняйте сообщения\n"
        "• ✅ Напоминания — не забывайте о важном\n"
        "• 📝 Заметки — записывайте идеи\n\n"
        "Разработано с ❤️ для пользователей Telegram",
        reply_markup=get_back_button("settings_menu")
    )
    await callback.answer()
