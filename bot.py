#!/usr/bin/env python3
"""
JARVIS Lite — Минималистичный бот для заметок
Приветствие: случайный язык | Умная фраза: только русский
"""
import os
import sys
import random
import asyncio
from datetime import datetime
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

# 🇷🇺 Умные фразы ТОЛЬКО на русском (20 вариантов)
SMART_PHRASES_RU = [
    "Записывай мысли — они имеют свойство улетучиваться ✨",
    "Лучшие идеи приходят тогда, когда их не ждёшь. Лови момент 🌱",
    "Память изменчива, а текст — вечный 📜",
    "Одна записанная идея стоит тысячи забытых гениальных мыслей 💫",
    "Творчество — это 1% вдохновения и 99% фиксации ✍️",
    "Сегодняшняя заметка — завтрашнее решение 🚀",
    "Мозг для идей, бот для хранения 🧠→🤖",
    "Не идея важна — важен момент, когда она пришла ⏳",
    "Хаос мыслей → порядок в заметках 🌪️→📋",
    "Ты — источник идей. Я — их архив 🌊→💾",
    "Заметка сегодня = благодарность себе завтра 🙏",
    "Идеи как птицы: поймай — иначе улетят 🕊️",
    "Тише едешь — дальше будешь. Тише думаешь — глубже запишешь 🐢",
    "Маленькая заметка — большой шаг к цели 🦶→🏔️",
    "Слова имеют вес. Записанные — вечность ⚖️",
    "Твори. Записывай. Повторяй 🔄",
    "Вдохновение не ждёт — успевай ловить 🦋",
    "Одна заметка — один шаг к порядку в голове 🧠",
    "Здесь безопасно хранить даже самые безумные идеи 😈",
    "Завтра ты забудешь. Я — нет 🤖"
]

# Эмодзи настроения
MOOD_EMOJIS = ["😊", "✨", "💫", "🌟", "🌿", "🍀", "🌱", "☀️", "🌙", "🍃"]

# ==================== БАЗА ДАННЫХ ====================
import sqlite3
from contextlib import contextmanager

DB_PATH = "jarvis.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                tags TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_user ON notes(user_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_tags ON notes(tags)')

def add_note(user_id: int, content: str, tags: str = "") -> int:
    with get_db() as conn:
        cursor = conn.execute(
            'INSERT INTO notes (user_id, content, tags) VALUES (?, ?, ?)',
            (user_id, content, tags)
        )
        return cursor.lastrowid

def get_notes(user_id: int, limit: int = 50):
    with get_db() as conn:
        cursor = conn.execute(
            'SELECT * FROM notes WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
            (user_id, limit)
        )
        return cursor.fetchall()

def search_notes(user_id: int, tag: str):
    with get_db() as conn:
        cursor = conn.execute(
            'SELECT * FROM notes WHERE user_id = ? AND tags LIKE ? ORDER BY created_at DESC',
            (user_id, f'%{tag}%')
        )
        return cursor.fetchall()

def extract_tags(text: str) -> str:
    """Извлекает #теги из текста → 'тег1,тег2'"""
    tags = []
    words = text.split()
    for word in words:
        if word.startswith('#') and len(word) > 1:
            tag = word[1:].strip('.,!?:;').lower()
            if tag and tag not in tags:
                tags.append(tag)
    return ','.join(tags[:5])

# Инициализация БД при старте
init_db()

# ==================== ЗАЩИТА ПОДПИСКИ ====================

async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    except (TelegramBadRequest, TelegramForbiddenError) as e:
        if "member list is inaccessible" in str(e):
            logger.warning(f"⚠️ Канал {REQUIRED_CHANNEL} недоступен — защита отключена")
            return True
        return False
    except Exception:
        return False

async def send_subscription_required(message: Message):
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
    if await is_subscribed(callback.from_user.id):
        await start_handler(callback.message)
        await callback.answer("✅ Доступ открыт!", show_alert=True)
    else:
        await callback.answer("❌ Подписка не найдена. Подпишитесь и попробуйте снова.", show_alert=True)

# ==================== КОМАНДЫ ====================

@dp.message(Command("start"))
async def start_handler(message: Message):
    if not await is_subscribed(message.from_user.id):
        await send_subscription_required(message)
        return
    
    flag, greeting_word = random.choice(GREETINGS)
    smart_phrase = random.choice(SMART_PHRASES_RU)
    mood = random.choice(MOOD_EMOJIS)
    
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
    await start_handler(callback.message)

@dp.callback_query(F.data == "search")
async def search_start(callback):
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
    logger.info("🚀 Запуск JARVIS Lite")
    logger.info(f"🤖 Бот: @{(await bot.get_me()).username}")
    logger.info(f"🔒 Обязательная подписка: {REQUIRED_CHANNEL}")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен")
    except Exception as e:
        logger.exception(f"❌ Критическая ошибка: {e}")
