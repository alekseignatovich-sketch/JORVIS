#!/usr/bin/env python3
"""
JARVIS Lite — Минималистичный бот для заметок
✅ Поддержка PostgreSQL + SQLite
🌍 Приветствие: случайный язык | 🇷🇺 Умная фраза: только русский
🔒 Обязательная подписка на канал @bot_pro_bot_you
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

# 🌍 Приветствия на 15 языках
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

# 🇷🇺 50 умных фраз на русском
SMART_PHRASES_RU = [
    # Философия мысли
    "Записывай мысли — они имеют свойство улетучиваться ✨",
    "Память изменчива, а текст — вечный 📜",
    "Мысль, не записанная вовремя, навсегда теряется в потоке сознания 🌊",
    "Голова для думания, бумага для записывания 🧠→📝",
    "Не ум умен, а запись умна 💡",
    "Мысль — это семя. Запись — это почва 🌱",
    "Тишина рождает мысли. Запись — бессмертие 🤫",
    "Мозг — процессор, заметки — оперативная память 💾",
    "Идея без записи — как сон без воспоминаний 💤",
    "Завтра ты забудешь. Я — нет 🤖",
    
    # Творчество и вдохновение
    "Лучшие идеи приходят тогда, когда их не ждёшь. Лови момент 🌱",
    "Творчество — это 1% вдохновения и 99% фиксации ✍️",
    "Вдохновение не ждёт — успевай ловить 🦋",
    "Искра гениальности гаснет за 7 секунд. Запиши быстрее ⚡",
    "Твори. Записывай. Повторяй 🔄",
    "Гений — это 10% вдохновения и 90% сохранённых черновиков 🎨",
    "Не жди музы — создавай сам и записывай мелодию 🎵",
    "Креативность любит порядок в заметках 🎨→📋",
    "Идея — это подарок. Запись — благодарность 🎁",
    "Творческий хаос требует цифрового порядка 🌪️→✨",
    
    # Практичность и продуктивность
    "Сегодняшняя заметка — завтрашнее решение 🚀",
    "Одна записанная идея стоит тысячи забытых гениальных мыслей 💫",
    "Маленькая заметка — большой шаг к цели 🦶→🏔️",
    "Не откладывай на потом то, что можно записать сейчас ⚡",
    "Порядок в заметках — порядок в голове 🧠✨",
    "Заметка сегодня = благодарность себе завтра 🙏",
    "Цель без плана — мечта. План без записи — иллюзия 🎯",
    "Делай. Записывай. Анализируй. Развивайся 📈",
    "Продуктивность начинается с одной заметки ✅",
    "Три вещи не вернуть: время, слово, упущенная идея ⏳",
    
    # Поэтичность и метафоры
    "Идеи как птицы: поймай — иначе улетят 🕊️",
    "Мысли текут рекой. Я строю плотины 🌊→💧",
    "Хаос мыслей → порядок в заметках 🌪️→📋",
    "Слова имеют вес. Записанные — вечность ⚖️",
    "Ты — автор. Я — черновик 📖",
    "От искры — к пламени. От заметки — к проекту 🔥",
    "Мир в твоих мыслях. Порядок — в моих заметках 🌍",
    "Звёзды гаснут. Записанные идеи — нет ✨",
    "Мысль — капля. Заметки — океан 💧→🌊",
    "Время стирает воспоминания. Текст — нет 🕰️",
    
    # Лёгкость и игривость
    "Мозг для идей, бот для хранения 🧠→🤖",
    "Ты думаешь — я запоминаю. Команда мечты! 🤝",
    "Здесь безопасно хранить даже самые безумные идеи 😈",
    "Одна заметка — один шаг к порядку в голове 🧠",
    "Ты — источник идей. Я — их архив 🌊→💾",
    "Не идея важна — важен момент, когда она пришла ⏳",
    "Здесь каждая идея имеет право на жизнь ✨",
    "Думай меньше о том, чтобы запомнить. Думай больше о том, чтобы создать 💭→🚀",
    "Я не судья твоих мыслей. Я — их друг 🤗",
    "Секреты надёжно спрятаны в твоих заметках 🔒",
    
    # Мудрость и глубина
    "Знание — сила. Записанное знание — могущество 💪",
    "Мудрый человек записывает. Гениальный — перечитывает 📚",
    "Прошлое учит, будущее зовёт. Настоящее — записывай 🔄",
    "Жизнь коротка. Заметки — вечны ⏳",
    "Не количество мыслей важно, а качество их сохранения 💎",
    "Мудрость не в том, чтобы знать всё. А в том, чтобы знать, где найти 🗺️",
    "Каждая великая вещь начиналась с маленькой заметки 📌",
    "Память обманчива. Текст — объективен 👁️",
    "Мысли уходят. Слова остаются. Мудрость — в записи 📜",
    "Завтрашний ты скажет спасибо сегодняшнему за эту заметку 🙏"
]

# Эмодзи настроения
MOOD_EMOJIS = ["😊", "✨", "💫", "🌟", "🌿", "🍀", "🌱", "☀️", "🌙", "🍃"]

# ==================== БАЗА ДАННЫХ (PostgreSQL + SQLite) ====================

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

# Создаём движок в зависимости от DATABASE_URL
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        connect_args={
            "connect_timeout": 10,
            "application_name": "jarvis-lite-bot"
        }
    )
    logger.info("✅ Подключено к PostgreSQL")
else:
    # SQLite для локальной разработки
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    logger.info("✅ Подключено к SQLite")

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

# Модель заметки
class Note(Base):
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    content = Column(Text, nullable=False)
    tags = Column(String, default="")  # CSV: "работа,идея,важное"
    created_at = Column(DateTime, default=func.now(), index=True)
    
    __table_args__ = (
        Index('idx_user_tags', 'user_id', 'tags'),
    )

# Создаём таблицы
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

def add_note(user_id: int, content: str, tags: str = "") -> int:
    """Создать заметку"""
    with get_db_session() as session:
        note = Note(user_id=user_id, content=content, tags=tags)
        session.add(note)
        session.flush()
        return note.id

def get_notes(user_id: int, limit: int = 50) -> List[Dict]:
    """Получить заметки пользователя"""
    with get_db_session() as session:
        notes = session.query(Note)\
            .filter(Note.user_id == user_id)\
            .order_by(Note.created_at.desc())\
            .limit(limit)\
            .all()
        return [{
            'id': n.id,
            'content': n.content[:100] + '...' if len(n.content) > 100 else n.content,
            'tags': n.tags.split(',') if n.tags else [],
            'created_at': n.created_at
        } for n in notes]

def search_notes(user_id: int, tag: str) -> List[Dict]:
    """Поиск заметок по тегу"""
    with get_db_session() as session:
        notes = session.query(Note)\
            .filter(
                Note.user_id == user_id,
                Note.tags.ilike(f'%{tag}%')
            )\
            .order_by(Note.created_at.desc())\
            .all()
        return [{
            'id': n.id,
            'content': n.content,
            'tags': n.tags.split(',') if n.tags else [],
            'created_at': n.created_at
        } for n in notes]

def extract_tags(text: str) -> str:
    """Извлекает #теги из текста → 'тег1,тег2'"""
    tags = []
    words = text.split()
    for word in words:
        if word.startswith('#') and len(word) > 1:
            tag = word[1:].strip('.,!?:;').lower()
            if tag and tag not in tags:
                tags.append(tag)
    return ','.join(tags[:5])  # Максимум 5 тегов

# ==================== ЗАЩИТА ПОДПИСКИ ====================

async def is_subscribed(user_id: int) -> bool:
    """Проверка подписки с безопасным обходом ошибок"""
    try:
        member = await bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    except (TelegramBadRequest, TelegramForbiddenError) as e:
        if "member list is inaccessible" in str(e):
            logger.warning(f"⚠️ Канал {REQUIRED_CHANNEL} недоступен — защита отключена")
            return True  # Пропускаем всех при ошибке канала
        return False
    except Exception:
        return False

async def send_subscription_required(message: Message):
    """Отправить сообщение с требованием подписки"""
    await message.answer(
        f"🔒 <b>Подписка обязательна</b>\n\n"
        f"Подпишитесь на канал, чтобы пользоваться ботом:\n"
        f"<a href='https://t.me/{REQUIRED_CHANNEL.lstrip('@')}'>@bot_pro_bot_you</a>\n\n"
        f"После подписки напишите /start",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📺 Перейти в канал", url="https://t.me/bot_pro_bot_you")],
            [InlineKeyboardButton(text="🔄 Проверить подписку", callback_data="check_sub")]
        ]),
        disable_web_page_preview=True
    )

@dp.callback_query(F.data == "check_sub")
async def check_sub(callback):
    """Проверка подписки по кнопке"""
    if await is_subscribed(callback.from_user.id):
        await start_handler(callback.message)
        await callback.answer("✅ Доступ открыт!", show_alert=True)
    else:
        await callback.answer("❌ Подписка не найдена. Подпишитесь и попробуйте снова.", show_alert=True)

# ==================== КОМАНДЫ ====================

@dp.message(Command("start"))
async def start_handler(message: Message):
    """Обработчик /start"""
    if not await is_subscribed(message.from_user.id):
        await send_subscription_required(message)
        return
    
    # 🌍 Случайное приветствие на любом языке
    flag, greeting_word = random.choice(GREETINGS)
    
    # 🇷🇺 Умная фраза ТОЛЬКО на русском
    smart_phrase = random.choice(SMART_PHRASES_RU)
    
    # Эмодзи настроения
    mood = random.choice(MOOD_EMOJIS)
    
    # Время суток
    hour = datetime.now().hour
    time_greeting = "Доброе утро" if 5 <= hour < 12 else "Добрый день" if 12 <= hour < 18 else "Добрый вечер"
    
    await message.answer(
        f"{mood} <b>{greeting_word}!</b> {flag}\n\n"
        f"<i>{smart_phrase}</i>\n\n"
        f"📝 <b>Как пользоваться:</b>\n"
        f"• Просто напиши заметку — она сохранится\n"
        f"• Добавь #теги для поиска (#работа #идея)\n"
        f"• Нажми 🔍 для поиска по тегам",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Поиск по тегам", callback_data="search")],
            [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")]
        ])
    )

@dp.callback_query(F.data == "help")
async def help_handler(callback):
    """Помощь"""
    await callback.message.edit_text(
        "💡 <b>Помощь</b>\n\n"
        "✨ <b>Сохранение заметок:</b>\n"
        "Просто напиши или перешли сообщение — оно сохранится автоматически.\n\n"
        "🏷️ <b>Теги:</b>\n"
        "Используй #теги в тексте:\n"
        "<code>Купить молоко #список #важное</code>\n"
        "Теги: <code>список</code>, <code>важное</code>\n\n"
        "🔍 <b>Поиск:</b>\n"
        "Нажми «🔍 Поиск» → введи тег без #:\n"
        "<code>работа</code> → покажет все заметки с #работа",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_start")
async def back_to_start(callback):
    """Вернуться в главное меню"""
    await start_handler(callback.message)

@dp.callback_query(F.data == "search")
async def search_start(callback):
    """Начать поиск"""
    await callback.message.edit_text(
        "🔍 <b>Поиск по тегам</b>\n\n"
        "Введите тег <b>без символа #</b>:\n"
        "Например: <code>работа</code> или <code>идея</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Отмена", callback_data="back_to_start")]
        ])
    )
    await callback.answer()

# ==================== СОХРАНЕНИЕ И ПОИСК ====================

user_search_state = {}

@dp.message()
async def universal_handler(message: Message):
    """Универсальный обработчик: сохранение заметок + поиск по тегам"""
    user_id = message.from_user.id
    
    # Проверка подписки для всех сообщений
    if not await is_subscribed(user_id):
        await send_subscription_required(message)
        return
    
    # Режим поиска
    if user_id in user_search_state and user_search_state[user_id] == "searching":
        del user_search_state[user_id]
        
        tag = message.text.strip().lower().lstrip('#')
        if not tag:
            await message.answer(
                "⚠️ Введите тег без #", 
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔍 Повторить поиск", callback_data="search")]
                ])
            )
            return
        
        results = search_notes(user_id, tag)
        
        if not results:
            await message.answer(
                f"📭 Нет заметок с тегом <code>#{tag}</code>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔍 Новый поиск", callback_data="search")],
                    [InlineKeyboardButton(text="⬅️ В меню", callback_data="back_to_start")]
                ])
            )
            return
        
        text = f"🔍 Найдено {len(results)} заметок с тегом <code>#{tag}</code>:\n\n"
        for i, note in enumerate(results[:10], 1):
            preview = note['content'][:80] + "..." if len(note['content']) > 80 else note['content']
            text += f"{i}. {preview}\n"
        
        if len(results) > 10:
            text += f"\n...и ещё {len(results) - 10} заметок"
        
        await message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Новый поиск", callback_data="search")],
                [InlineKeyboardButton(text="⬅️ В меню", callback_data="back_to_start")]
            ])
        )
        return
    
    # Обычное сохранение заметки
    content = message.text or message.caption or ""
    if message.photo:
        content = (message.caption or "") + "\n[🖼️ Фото]"
    elif message.document:
        content = (message.caption or "") + f"\n[📄 {message.document.file_name}]"
    elif message.video:
        content = (message.caption or "") + "\n[🎬 Видео]"
    elif message.voice:
        content = (message.caption or "") + "\n[🎤 Голосовое]"
    
    if not content.strip():
        await message.reply("💭 Пустые сообщения не сохраняю. Напиши что-нибудь интересное!")
        return
    
    tags = extract_tags(content)
    note_id = add_note(user_id, content, tags)
    mood = random.choice(["✅", "✨", "💫", "🌟", "🌿"])
    tag_text = f"\n🏷️ Теги: #{' #'.join(tags.split(','))}" if tags else ""
    
    await message.reply(
        f"{mood} Сохранено! (#{note_id}){tag_text}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Поиск по тегам", callback_data="search")],
            [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")]
        ])
    )

# ==================== ЗАПУСК ====================

async def main():
    """Основная функция запуска"""
    logger.info("🚀 Запуск JARVIS Lite")
    logger.info(f"🤖 Бот: @{(await bot.get_me()).username}")
    logger.info(f"🔒 Обязательная подписка: {REQUIRED_CHANNEL}")
    logger.info(f"💾 База данных: {DATABASE_URL}")
    
    # Тест подключения к БД
    try:
        test_id = add_note(123456, "Тестовая заметка", "тест")
        logger.info(f"✅ База данных работает (тестовая заметка ID: {test_id})")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.exception(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
