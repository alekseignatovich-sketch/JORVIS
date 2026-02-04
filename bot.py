#!/usr/bin/env python3
"""
JARVIS — Telegram Personal Assistant Bot
MVP Version 1.0 — Рабочая версия
"""
import sys
import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger
from dotenv import load_dotenv

# 🔑 Добавляем корень проекта в PYTHONPATH (защита от ошибок импорта)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Загрузка .env (для локальной разработки)
if os.path.exists(".env"):
    load_dotenv()

# Настройка логирования
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)

# Импорты из корня проекта
try:
    from database import db
    logger.info("✅ Модуль 'database' успешно импортирован")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта 'database': {e}")
    logger.error(f"Текущая директория: {os.getcwd()}")
    logger.error(f"Содержимое директории: {os.listdir('.')}")
    sys.exit(1)

try:
    from keyboards import get_main_menu, get_back_button
    from handlers.bookmarks import router as bookmarks_router, save_bookmark_simple
    from handlers.reminders import router as reminders_router, show_reminders_simple
    from handlers.notes import router as notes_router, show_notes_simple
    from handlers.settings import router as settings_router
    logger.info("✅ Все модули успешно импортированы")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта модулей: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Инициализация бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не найден! Установите переменную окружения BOT_TOKEN в Railway")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Регистрация роутеров
dp.include_router(bookmarks_router)
dp.include_router(reminders_router)
dp.include_router(notes_router)
dp.include_router(settings_router)

# ==================== КОМАНДЫ ====================

@dp.message(Command("start"))
async def start_handler(message: Message):
    db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        language_code=message.from_user.language_code
    )
    
    await message.answer(
        "🤖 <b>Привет! Я JARVIS</b>\n\n"
        "Ваш персональный ассистент внутри Telegram.\n\n"
        "<b>Что я умею:</b>\n"
        "• 📌 Сохранять сообщения в закладки\n"
        "• ✅ Напоминать о важных делах\n"
        "• 📝 Создавать заметки и списки\n\n"
        "Выберите раздел ниже 👇",
        reply_markup=get_main_menu()
    )

@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "<b>📖 Помощь</b>\n\n"
        "<b>📌 Закладки</b>\n"
        "Перешлите любое сообщение мне — я сохраню его.\n"
        "Или напишите текст — он тоже сохранится.\n\n"
        "<b>✅ Напоминания</b>\n"
        "Напишите: <code>напомни завтра в 10 позвонить маме</code>\n\n"
        "<b>📝 Заметки</b>\n"
        "Создавайте заметки через меню → «📝 Заметки».\n\n"
        "Есть вопросы? Пишите!",
        reply_markup=get_main_menu()
    )

@dp.message(Command("bookmarks"))
async def bookmarks_command(message: Message):
    """Показать закладки через команду"""
    bookmarks = db.get_bookmarks(message.from_user.id, limit=20)
    
    if not bookmarks:
        text = "📭 У вас пока нет закладок.\n\nПерешлите любое сообщение мне, чтобы сохранить его!"
        await message.answer(text, reply_markup=get_back_button("bookmarks_menu"))
        return
    
    text = "📌 <b>Ваши закладки</b>:\n\n"
    for i, bm in enumerate(bookmarks[:10], 1):
        content = bm['message_text'][:50] + "..." if bm['message_text'] and len(bm['message_text']) > 50 else bm['message_text']
        text += f"{i}. {content or '📎 Файл/медиа'}\n"
    
    if len(bookmarks) > 10:
        text += f"\n...и ещё {len(bookmarks) - 10} закладок"
    
    await message.answer(text, reply_markup=get_back_button("bookmarks_menu"))

@dp.message(Command("reminders"))
async def reminders_command(message: Message):
    """Показать напоминания через команду"""
    await show_reminders_simple(message)

@dp.message(Command("notes"))
async def notes_command(message: Message):
    """Показать заметки через команду"""
    await show_notes_simple(message)

# ==================== CALLBACKS ====================

@dp.callback_query(lambda c: c.data == "menu_main")
async def back_to_main(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            "🤖 <b>JARVIS — Главное меню</b>\n\n"
            "Выберите раздел:",
            reply_markup=get_main_menu()
        )
    except Exception:
        await callback.message.answer(
            "🤖 <b>JARVIS — Главное меню</b>\n\n"
            "Выберите раздел:",
            reply_markup=get_main_menu()
        )
    await callback.answer()

# ==================== ОСНОВНОЙ ОБРАБОТЧИК ТЕКСТА ====================

@dp.message()
async def handle_text(message: Message):
    """Авто-определение типа сообщения"""
    if not message.text:
        # Если нет текста (фото/документ без подписи) — сохраняем как закладку
        await save_bookmark_simple(message)
        return
        
    text_lower = message.text.lower()
    
    # Распознавание напоминаний
    reminder_triggers = ["напомни", "напомнить", "напомни мне"]
    if any(trigger in text_lower for trigger in reminder_triggers):
        from handlers.reminders import add_reminder_start, ReminderStates
        from aiogram.fsm.context import FSMContext
        
        state = FSMContext(storage=dp.storage, chat_id=message.chat.id, user_id=message.from_user.id)
        
        class FakeCallback:
            def __init__(self, msg):
                self.message = msg
                self.answer = lambda: None
        
        await add_reminder_start(FakeCallback(message), state)
        await state.set_state(ReminderStates.waiting_for_text)
        return
    
    # Сохранение как закладки
    await save_bookmark_simple(message)

# ==================== ФОНОВАЯ ЗАДАЧА ====================

async def check_reminders_task():
    """Проверка напоминаний каждую минуту"""
    while True:
        try:
            due = db.get_due_reminders()
            for reminder in due:
                try:
                    await bot.send_message(
                        chat_id=reminder['user_id'],
                        text=f"⏰ <b>Напоминание!</b>\n\n{reminder['text']}"
                    )
                    db.mark_reminder_completed(reminder['id'])
                    logger.info(f"✅ Отправлено напоминание #{reminder['id']} пользователю {reminder['user_id']}")
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки напоминания {reminder['id']}: {e}")
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"❌ Ошибка в фоновой задаче: {e}")
            await asyncio.sleep(60)

# ==================== ЗАПУСК ====================

async def main():
    logger.info("🚀 Запуск бота JARVIS...")
    logger.info(f"🤖 Bot: @{(await bot.get_me()).username}")
    
    # Проверка подключения к БД
    try:
        stats = db.get_user_stats(123456789)
        logger.info("✅ Подключение к базе данных установлено")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        sys.exit(1)
    
    # Запуск фоновой задачи
    asyncio.create_task(check_reminders_task())
    
    # Запуск поллинга
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.exception(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
