#!/usr/bin/env python3
"""
JARVIS Lite — Ультра-минималистичные заметки
✅ Без тегов — просто текст
✅ При каждом сообщении: «✅ Сохранено!»
✅ Простой поиск по тексту заметок
✅ Минимализм: только кнопка «🔍 Поиск»
🔒 Обязательная подписка на @bot_pro_bot_you
"""
import os
import sys
import random
import asyncio
from datetime import datetime
from typing import List, Dict
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from loguru import logger
from dotenv import load_dotenv

# Настройка логирования
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>", level="INFO")

# Загрузка переменных
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "@bot_pro_bot_you")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./jarvis.db")

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не задан!")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 🌍 Приветствия на 15 языках (только приветствие)
GREETINGS = [
    ("🇷🇺", "Привет"),
    ("🇺🇸", "Hello"),
    ("🇪🇸", "¡Hola"),
    ("🇫🇷", "Bonjour"),
    ("🇩🇪", "Hallo"),
    ("🇮🇹", "Ciao"),
    ("🇵🇹", "Olá"),
    ("🇳🇱", "Hallo"),
    ("🇸🇪", "Hej"),
    ("🇯🇵", "こんにちは"),
    ("🇨🇳", "你好"),
    ("🇰🇷", "안녕하세요"),
    ("🇮🇳", "नमस्ते"),
    ("🇦🇪", "مرحباً"),
    ("🇹🇷", "Merhaba"),
]

# 🇷🇺 20 умных фраз на русском (только для приветствия)
SMART_PHRASES_RU = [
    "Записывай мысли — они имеют свойство улетучиваться ✨",
    "Память изменчива, а текст — вечный 📜",
    "Лучшие идеи приходят тогда, когда их не ждёшь 🌱",
    "Одна записанная идея стоит тысячи забытых 💫",
    "Сегодняшняя заметка — завтрашнее решение 🚀",
    "Мозг для идей, бот для хранения 🧠→🤖",
    "Идеи как птицы: поймай — иначе улетят 🕊️",
    "Хаос мыслей → порядок в заметках 🌪️→📋",
    "Ты — источник идей. Я — их архив 🌊→💾",
    "Завтра ты забудешь. Я — нет 🤖",
    "Маленькая заметка — большой шаг к цели 🦶→🏔️",
    "Слова имеют вес. Записанные — вечность ⚖️",
    "От искры — к пламени. От заметки — к проекту 🔥",
    "Время стирает воспоминания. Текст — нет 🕰️",
    "Здесь безопасно хранить даже самые безумные идеи 😈",
    "Одна заметка — один шаг к порядку в голове 🧠",
    "Знание — сила. Записанное знание — могущество 💪",
    "Каждая великая вещь начиналась с маленькой заметки 📌",
    "Мысли уходят. Слова остаются. Мудрость — в записи 📜",
    "Завтрашний ты скажет спасибо сегодняшнему за эту заметку 🙏"
]

# Состояния пользователей для поиска
user_search_state = {}

# ==================== БАЗА ДАННЫХ ====================

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        connect_args={"connect_timeout": 10}
    )
    logger.info("✅ Подключено к PostgreSQL")
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    logger.info("✅ Подключено к SQLite")

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), index=True)

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    last_active = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

Base.metadata.create_all(bind=engine)
logger.info("✅ Таблицы созданы / проверены")

@contextmanager
def get_db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def add_note(user_id: int, content: str) -> int:
    """Сохранить заметку БЕЗ тегов"""
    with get_db_session() as session:
        note = Note(user_id=user_id, content=content)
        session.add(note)
        session.flush()
        return note.id

def get_notes(user_id: int, limit: int = 50) -> List[Dict]:
    """Получить последние заметки"""
    with get_db_session() as session:
        notes = session.query(Note)\
            .filter(Note.user_id == user_id)\
            .order_by(Note.created_at.desc())\
            .limit(limit)\
            .all()
        return [{
            'id': n.id,
            'content': n.content[:100] + '...' if len(n.content) > 100 else n.content,
            'created_at': n.created_at
        } for n in notes]

def search_notes(user_id: int, query: str) -> List[Dict]:
    """Простой поиск по тексту заметок"""
    with get_db_session() as session:
        notes = session.query(Note)\
            .filter(
                Note.user_id == user_id,
                Note.content.ilike(f'%{query}%')
            )\
            .order_by(Note.created_at.desc())\
            .all()
        return [{
            'id': n.id,
            'content': n.content[:120] + '...' if len(n.content) > 120 else n.content,
            'created_at': n.created_at
        } for n in notes]

def get_or_create_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """Получить или создать пользователя"""
    with get_db_session() as session:
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            session.add(user)
            session.flush()
            return {'user_id': user.user_id, 'first_name': user.first_name}
        else:
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.last_active = datetime.now()
            session.flush()
            return {'user_id': user.user_id, 'first_name': user.first_name}

# ==================== ЗАЩИТА ПОДПИСКИ ====================

async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    except (TelegramBadRequest, TelegramForbiddenError):
        return True  # При ошибке канала — пропускаем (защита не критична)
    except Exception:
        return False

async def send_subscription_required(message: Message):
    await message.answer(
        f"🔒 <b>Подписка обязательна</b>\n\n"
        f"Подпишитесь на канал, чтобы пользоваться ботом:\n"
        f"<a href='https://t.me/{REQUIRED_CHANNEL.lstrip('@')}'>@bot_pro_bot_you</a>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📺 Перейти в канал", url="https://t.me/bot_pro_bot_you")],
            [InlineKeyboardButton(text="🔄 Проверить подписку", callback_data="check_sub")]
        ]),
        disable_web_page_preview=True
    )

@dp.callback_query(F.data == "check_sub")
async def check_sub(callback):
    if await is_subscribed(callback.from_user.id):
        await start_handler(callback.message)
        await callback.answer("✅ Доступ открыт!", show_alert=True)
    else:
        await callback.answer("❌ Подписка не найдена. Подпишитесь и попробуйте снова.", show_alert=True)

# ==================== КЛАВИАТУРЫ ====================

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Только одна кнопка — поиск (как в заметках Viber)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="search")]
    ])

def get_search_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_search")]
    ])

# ==================== КОМАНДЫ ====================

@dp.message(Command("start"))
async def start_handler(message: Message):
    if not await is_subscribed(message.from_user.id):
        await send_subscription_required(message)
        return
    
    # Сохраняем пользователя
    user = get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name
    )
    
    # 🌍 Приветствие на случайном языке
    flag, greeting_word = random.choice(GREETINGS)
    
    # 🇷🇺 Умная фраза на русском
    smart_phrase = random.choice(SMART_PHRASES_RU)
    
    # Имя для обращения
    name = user['first_name'] or "друг"
    name = name.split()[0]
    
    # Отправляем приветствие
    await message.answer(
        f"👋 <b>{greeting_word}, {name}!</b> {flag}\n\n"
        f"<i>{smart_phrase}</i>\n\n"
        "📝 Просто пиши — я сохраню.\n"
        "🔍 Нажми кнопку ниже, чтобы найти заметку.",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "💡 <b>Как пользоваться</b>\n\n"
        "✨ <b>Сохранение:</b>\n"
        "Просто напиши или перешли сообщение — я сохраню его.\n\n"
        "🔍 <b>Поиск:</b>\n"
        "Нажми «🔍 Поиск» → введи слово или фразу → я покажу подходящие заметки.",
        reply_markup=get_main_keyboard()
    )

# ==================== ПОИСК ====================

@dp.callback_query(F.data == "search")
async def search_start(callback):
    user_search_state[callback.from_user.id] = "searching"
    await callback.message.edit_text(
        "🔍 <b>Поиск</b>\n\n"
        "Введите слово или фразу для поиска:",
        reply_markup=get_search_cancel_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "cancel_search")
async def cancel_search(callback):
    user_id = callback.from_user.id
    if user_id in user_search_state:
        del user_search_state[user_id]
    await start_handler(callback.message)

@dp.message()
async def message_handler(message: Message):
    user_id = message.from_user.id
    
    # Проверка подписки
    if not await is_subscribed(user_id):
        await send_subscription_required(message)
        return
    
    # Сохраняем пользователя
    get_or_create_user(
        user_id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name
    )
    
    # Режим поиска
    if user_id in user_search_state and user_search_state[user_id] == "searching":
        del user_search_state[user_id]
        
        query = message.text.strip()
        if not query:
            await message.answer("⚠️ Введите текст для поиска", reply_markup=get_search_cancel_keyboard())
            return
        
        results = search_notes(user_id, query)
        
        if not results:
            await message.answer(
                f"📭 Не найдено заметок по запросу «<code>{query}</code>»",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Формируем результаты
        text = f"✅ Найдено {len(results)} заметок:\n\n"
        for i, note in enumerate(results[:10], 1):
            text += f"{i}. {note['content']}\n\n"
        
        if len(results) > 10:
            text += f"...и ещё {len(results) - 10} заметок"
        
        await message.answer(text, reply_markup=get_main_keyboard())
        return
    
    # === СОХРАНЕНИЕ ЗАМЕТКИ ===
    content = message.text or message.caption or ""
    
    # Обработка медиа
    if message.photo:
        content = (message.caption or "") + "\n[🖼️ Фото]"
    elif message.document:
        content = (message.caption or "") + f"\n[📄 {message.document.file_name}]"
    elif message.video:
        content = (message.caption or "") + "\n[🎬 Видео]"
    elif message.voice:
        content = (message.caption or "") + "\n[🎤 Голосовое]"
    
    if not content.strip():
        await message.reply("💭 Пустые сообщения не сохраняю")
        return
    
    # Сохраняем БЕЗ тегов
    note_id = add_note(user_id, content)
    
    # ✅ Мгновенное подтверждение
    await message.reply("✅ Сохранено!", reply_markup=get_main_keyboard())

# ==================== ЗАПУСК ====================

async def main():
    logger.info("🚀 Запуск JARVIS Lite (ультра-минимализм)")
    logger.info(f"🤖 Бот: @{(await bot.get_me()).username}")
    logger.info(f"🔒 Подписка: {REQUIRED_CHANNEL}")
    logger.info(f"💾 База данных: {DATABASE_URL}")
    
    # Тест БД
    try:
        test_id = add_note(123456, "Тестовая заметка")
        logger.info(f"✅ База данных работает (тестовая заметка ID: {test_id})")
    except Exception as e:
        logger.error(f"❌ Ошибка БД: {e}")
        sys.exit(1)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен")
    except Exception as e:
        logger.exception(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
