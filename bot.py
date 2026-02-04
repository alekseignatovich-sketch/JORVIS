import asyncio
import logging
import sys
import os
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>")

# Импорт модулей
from database import db
from keyboards import get_main_menu
from handlers import bookmarks, reminders, notes, settings

# Инициализация бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден! Проверьте .env файл")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Регистрация роутеров
dp.include_router(bookmarks.router)
dp.include_router(reminders.router)
dp.include_router(notes.router)
dp.include_router(settings.router)

# ==================== КОМАНДЫ ====================

@dp.message(Command("start"))
async def start_handler(message: Message):
    # Сохраняем пользователя в БД
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
        "• 📝 Создавать заметки и списки\n"
        "• 🤖 Помогать с текстами (скоро)\n\n"
        "Выберите раздел ниже 👇",
        reply_markup=get_main_menu()
    )

@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "<b>📖 Помощь</b>\n\n"
        "<b>📌 Закладки</b>\n"
        "Перешлите любое сообщение мне — я сохраню его.\n\n"
        "<b>✅ Напоминания</b>\n"
        "Напишите: <code>напомни завтра в 10 позвонить маме</code>\n\n"
        "<b>📝 Заметки</b>\n"
        "Создавайте заметки для идей и планов.\n\n"
        "<b>⚙️ Настройки</b>\n"
        "Измените язык и узнайте о боте.\n\n"
        "Есть вопросы? Пишите!",
        reply_markup=get_main_menu()
    )

@dp.message(Command("bookmarks"))
async def bookmarks_command(message: Message):
    from handlers.bookmarks import show_bookmarks
    # Создаём фейковый callback
    class FakeCallback:
        def __init__(self, msg):
            self.message = msg
            self.from_user = msg.from_user
            self.answer = lambda: None
    
    fake_callback = FakeCallback(message)
    await show_bookmarks(fake_callback)

@dp.message(Command("reminders"))
async def reminders_command(message: Message):
    from handlers.reminders import show_reminders
    class FakeCallback:
        def __init__(self, msg):
            self.message = msg
            self.from_user = msg.from_user
            self.answer = lambda: None
    
    fake_callback = FakeCallback(message)
    await show_reminders(fake_callback)

@dp.message(Command("notes"))
async def notes_command(message: Message):
    from handlers.notes import show_notes
    class FakeCallback:
        def __init__(self, msg):
            self.message = msg
            self.from_user = msg.from_user
            self.answer = lambda: None
    
    fake_callback = FakeCallback(message)
    await show_notes(fake_callback)

# ==================== CALLBACKS ====================

@dp.callback_query(lambda c: c.data == "menu_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text(
        "🤖 <b>JARVIS — Главное меню</b>\n\n"
        "Выберите раздел:",
        reply_markup=get_main_menu()
    )
    await callback.answer()

# ==================== ОБРАБОТКА ТЕКСТА ====================

@dp.message()
async def handle_text(message: Message):
    """Обработка обычного текста (не команда)"""
    text = message.text.lower()
    
    # Авто-определение: напоминание?
    if any(word in text for word in ["напомни", "напомнить", "напомни мне", "remember"]):
        from handlers.reminders import add_reminder_start, ReminderStates
        from aiogram.fsm.context import FSMContext
        
        state = FSMContext(storage=dp.storage, chat_id=message.chat.id, user_id=message.from_user.id)
        await add_reminder_start(
            type('obj', (object,), {
                'message': message,
                'answer': lambda: None
            })(), 
            state
        )
        await state.set_state(ReminderStates.waiting_for_text)
        return
    
    # Иначе — сохраняем как закладку
    from handlers.bookmarks import save_bookmark
    await save_bookmark(message, None)

# ==================== ФОНОВАЯ ЗАДАЧА: ПРОВЕРКА НАПОМИНАНИЙ ====================

async def check_reminders():
    """Проверяет, есть ли напоминания, которые нужно отправить"""
    while True:
        try:
            due_reminders = db.get_due_reminders()
            
            for reminder in due_reminders:
                try:
                    await bot.send_message(
                        chat_id=reminder['user_id'],
                        text=f"⏰ <b>Напоминание!</b>\n\n{reminder['text']}"
                    )
                    db.mark_reminder_completed(reminder['id'])
                except Exception as e:
                    logger.error(f"Не удалось отправить напоминание {reminder['id']}: {e}")
            
            await asyncio.sleep(60)  # Проверяем каждую минуту
        except Exception as e:
            logger.error(f"Ошибка в фоновой задаче: {e}")
            await asyncio.sleep(60)

# ==================== ЗАПУСК ====================

async def main():
    logger.info("🚀 Запуск бота JARVIS...")
    
    # Запуск фоновой задачи
    asyncio.create_task(check_reminders())
    
    # Запуск поллинга
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")
        sys.exit(1)
