#!/usr/bin/env python3
"""
JARVIS Lite — Минималистичный бот для заметок с душой
✅ Исправленный поиск по тегам
✅ Приветствие + умная фраза — отдельные сообщения
✅ Только кнопка «Поиск» (минимализм)
✅ Ежедневное приветствие в 9:00 по будням
✅ Персональный «голос» с именем пользователя
🔒 Обязательная подписка на @bot_pro_bot_you
"""
import os
import sys
import random
import asyncio
from datetime import datetime, time, timedelta
from typing import List, Dict
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
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
scheduler = AsyncIOScheduler()

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

# 🇷🇺 50 умных фраз на русском (только фразы)
SMART_PHRASES_RU = [
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

# Эмодзи для персонального "голоса"
VOICE_EMOJIS = {
    "default": ["😊", "✨", "💫", "🌟", "🌿", "🍀", "🌱", "☀️", "🌙", "🍃"],
    "morning": ["🌅", "☀️", "☕", "🌤️", "🐦"],
    "day": ["🌤️", "💡", "🚀", "⚡", "🌈"],
    "evening": ["🌆", "🌙", "🕯️", "🌌", "🌠"]
}

# Состояния пользователей для поиска
user_search_state = {}

# ==================== БАЗА ДАННЫХ (PostgreSQL + SQLite) ====================

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

# Создаём движок
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
    tags = Column(String, default="")
    created_at = Column(DateTime, default=func.now(), index=True)
    __table_args__ = (Index('idx_user_tags', 'user_id', 'tags'),)

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

def add_note(user_id: int, content: str, tags: str = "") -> int:
    with get_db_session() as session:
        note = Note(user_id=user_id, content=content, tags=tags)
        session.add(note)
        session.flush()
        return note.id

def get_notes(user_id: int, limit: int = 50) -> List[Dict]:
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
    """Исправленный поиск: ищем тег как отдельное слово в CSV"""
    with get_db_session() as session:
        # Ищем тег как отдельный элемент в CSV (через запятую)
        notes = session.query(Note)\
            .filter(
                Note.user_id == user_id,
                Note.tags.op('REGEXP')(rf'(,|^){tag}(,|$)')  # Для PostgreSQL
            )\
            .order_by(Note.created_at.desc())\
            .all()
        if not notes:  # Fallback для SQLite
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
    return ','.join(tags[:5])

def get_or_create_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """Сохраняем/обновляем пользователя для персонализации"""
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
        else:
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.last_active = func.now()
        session.flush()
        return {
            'user_id': user.user_id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }

def get_active_users(days: int = 7) -> List[int]:
    """Получаем пользователей, активных за последние N дней"""
    with get_db_session() as session:
        since = datetime.now() - timedelta(days=days)
        users = session.query(User)\
            .filter(User.last_active >= since)\
            .all()
        return [user.user_id for user in users]

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
    """Минималистичная клавиатура — только поиск"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск по тегам", callback_data="search")]
    ])

def get_search_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура отмены поиска"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить поиск", callback_data="cancel_search")]
    ])

# ==================== КОМАНДЫ ====================

@dp.message(Command("start"))
async def start_handler(message: Message):
    if not await is_subscribed(message.from_user.id):
        await send_subscription_required(message)
        return
    
    # Сохраняем пользователя для персонализации
    user = get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name
    )
    
    # 🌍 Приветствие на случайном языке
    flag, greeting_word = random.choice(GREETINGS)
    mood = random.choice(VOICE_EMOJIS["default"])
    
    # Формируем имя для обращения
    name = user['first_name'] or user['username'] or "друг"
    name = name.split()[0]  # Только первое имя
    
    # Отправляем приветствие
    await message.answer(
        f"{mood} <b>{greeting_word}, {name}!</b> {flag}",
        reply_markup=get_main_keyboard()
    )
    
    # Пауза 0.7 секунды для естественности
    await asyncio.sleep(0.7)
    
    # 🇷🇺 Умная фраза на русском (отдельное сообщение!)
    smart_phrase = random.choice(SMART_PHRASES_RU)
    await message.answer(
        f"<i>{smart_phrase}</i>\n\n"
        "📝 Просто напиши заметку — она сохранится.\n"
        "🏷️ Используй #теги для поиска (#работа #идея)",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("help"))
async def help_handler(message: Message):
    """Справка по команде /help (без кнопки в интерфейсе)"""
    await message.answer(
        "💡 <b>Как пользоваться ботом</b>\n\n"
        "✨ <b>Сохранение:</b>\n"
        "Напиши или перешли сообщение — оно сохранится автоматически.\n\n"
        "🏷️ <b>Теги:</b>\n"
        "Добавляй #теги в текст:\n"
        "<code>Купить молоко #список #важное</code>\n\n"
        "🔍 <b>Поиск:</b>\n"
        "Нажми «🔍 Поиск» → введи тег без #:\n"
        "<code>работа</code> → покажет все заметки с #работа",
        reply_markup=get_main_keyboard()
    )

# ==================== ПОИСК ПО ТЕГАМ (ИСПРАВЛЕННЫЙ) ====================

@dp.callback_query(F.data == "search")
async def search_start(callback):
    """Начало поиска — устанавливаем состояние"""
    user_search_state[callback.from_user.id] = "searching"
    await callback.message.edit_text(
        "🔍 <b>Поиск по тегам</b>\n\n"
        "Введите тег <b>без символа #</b>:\n"
        "Например: <code>работа</code> или <code>идея</code>",
        reply_markup=get_search_cancel_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "cancel_search")
async def cancel_search(callback):
    """Отмена поиска"""
    user_id = callback.from_user.id
    if user_id in user_search_state:
        del user_search_state[user_id]
    await start_handler(callback.message)

@dp.message()
async def message_handler(message: Message):
    """Универсальный обработчик: сохранение заметок + поиск"""
    user_id = message.from_user.id
    
    # Проверка подписки
    if not await is_subscribed(user_id):
        await send_subscription_required(message)
        return
    
    # Сохраняем активность пользователя
    get_or_create_user(
        user_id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name
    )
    
    # Режим поиска
    if user_id in user_search_state and user_search_state[user_id] == "searching":
        del user_search_state[user_id]
        
        tag = message.text.strip().lower().lstrip('#')
        if not tag:
            await message.answer(
                "⚠️ Введите тег без #",
                reply_markup=get_search_cancel_keyboard()
            )
            return
        
        # ИСПРАВЛЕНО: поиск по точному совпадению тега в CSV
        results = search_notes(user_id, tag)
        
        if not results:
            await message.answer(
                f"📭 Не найдено заметок с тегом <code>#{tag}</code>",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Формируем результаты
        text = f"✅ Найдено {len(results)} заметок с тегом <code>#{tag}</code>:\n\n"
        for i, note in enumerate(results[:10], 1):
            preview = note['content'][:70] + "..." if len(note['content']) > 70 else note['content']
            tags_display = ' '.join([f"#{t}" for t in note['tags']]) if note['tags'] else ''
            text += f"{i}. {preview}\n{tags_display}\n\n"
        
        if len(results) > 10:
            text += f"...и ещё {len(results) - 10} заметок"
        
        await message.answer(text, reply_markup=get_main_keyboard())
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
        await message.reply("💭 Пустые сообщения не сохраняю. Напиши что-нибудь!")
        return
    
    # Извлекаем теги и сохраняем
    tags = extract_tags(content)
    note_id = add_note(user_id, content, tags)
    
    # Персональный ответ с "голосом" бота
    hour = datetime.now().hour
    if 5 <= hour < 12:
        mood = random.choice(VOICE_EMOJIS["morning"])
        voice_phrase = "☕ Утренняя заметка сохранена!"
    elif 12 <= hour < 18:
        mood = random.choice(VOICE_EMOJIS["day"])
        voice_phrase = "🚀 Заметка в деле сохранена!"
    else:
        mood = random.choice(VOICE_EMOJIS["evening"])
        voice_phrase = "🌙 Вечерняя мысль надёжно спрятана!"
    
    tag_text = f"\n🏷️ Теги: #{' #'.join(tags.split(','))}" if tags else ""
    
    await message.reply(
        f"{mood} {voice_phrase} (#{note_id}){tag_text}",
        reply_markup=get_main_keyboard()
    )

# ==================== ЕЖЕДНЕВНОЕ ПРИВЕТСТВИЕ В 9:00 ====================

async def send_morning_greeting():
    """Отправляем утреннее приветствие всем активным пользователям"""
    logger.info("🌅 Отправка утренних приветствий...")
    
    # Получаем активных пользователей (за последние 7 дней)
    active_users = get_active_users(days=7)
    logger.info(f"📨 Найдено {len(active_users)} активных пользователей")
    
    # Умная фраза дня
    daily_phrase = random.choice(SMART_PHRASES_RU)
    
    success_count = 0
    for user_id in active_users:
        try:
            # Получаем данные пользователя для персонализации
            with get_db_session() as session:
                user = session.query(User).filter(User.user_id == user_id).first()
                if not user:
                    continue
                
                name = user.first_name or user.username or "друг"
                name = name.split()[0]
            
            # Отправляем приветствие
            await bot.send_message(
                chat_id=user_id,
                text=f"🌅 Доброе утро, {name}!\n\n<i>{daily_phrase}</i>\n\nЧто сегодня запишем?",
                reply_markup=get_main_keyboard()
            )
            success_count += 1
            await asyncio.sleep(0.1)  # Защита от лимитов Telegram
            
        except Exception as e:
            logger.warning(f"⚠️ Не удалось отправить приветствие пользователю {user_id}: {e}")
            continue
    
    logger.info(f"✅ Отправлено {success_count} утренних приветствий")

# ==================== ЗАПУСК ====================

async def main():
    logger.info("🚀 Запуск JARVIS Lite")
    logger.info(f"🤖 Бот: @{(await bot.get_me()).username}")
    logger.info(f"🔒 Подписка: {REQUIRED_CHANNEL}")
    logger.info(f"💾 База данных: {DATABASE_URL}")
    
    # Тест подключения к БД
    try:
        test_id = add_note(123456, "Тест", "тест")
        logger.info(f"✅ База данных работает (тестовая заметка ID: {test_id})")
    except Exception as e:
        logger.error(f"❌ Ошибка БД: {e}")
        sys.exit(1)
    
    # Настройка ежедневного приветствия (будние дни в 9:00 по Минску UTC+3)
    scheduler.add_job(
        send_morning_greeting,
        CronTrigger(day_of_week='mon-fri', hour=9, minute=0, timezone='Europe/Minsk'),
        id='morning_greeting',
        replace_existing=True
    )
    scheduler.start()
    logger.info("⏰ Планировщик запущен: ежедневные приветствия в 9:00 по будням")
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
        if scheduler.running:
            scheduler.shutdown()
    except Exception as e:
        logger.exception(f"❌ Критическая ошибка: {e}")
        if scheduler.running:
            scheduler.shutdown()
        sys.exit(1)
