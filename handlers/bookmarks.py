from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatMemberStatus
from database import db
from keyboards import get_bookmarks_menu, get_back_button

router = Router()

# 🔑 Константа канала (должна совпадать с .env)
REQUIRED_CHANNEL = "@bot_pro_bot_you"

# 🔑 Функция проверки подписки
async def is_subscribed(bot: Bot, user_id: int) -> bool:
    """Проверить, подписан ли пользователь на канал"""
    try:
        chat_member = await bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return chat_member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR
        ]
    except Exception as e:
        return False

# FSM для добавления закладки
class BookmarkStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_tags = State()

@router.callback_query(F.data == "bookmarks_menu")
async def bookmarks_menu(callback: CallbackQuery, bot: Bot):
    # 🔑 Проверка подписки
    if not await is_subscribed(bot, callback.from_user.id):
        await callback.answer("🔒 Для доступа к функциям бота подпишитесь на канал @bot_pro_bot_you", show_alert=True)
        return
    
    try:
        await callback.message.edit_text(
            "📌 <b>Закладки</b>\n\n"
            "Сохраняйте важные сообщения, ссылки, фото — всё в одном месте.\n\n"
            "Выберите действие:",
            reply_markup=get_bookmarks_menu()
        )
    except Exception:
        await callback.message.answer(
            "📌 <b>Закладки</b>\n\n"
            "Сохраняйте важные сообщения, ссылки, фото — всё в одном месте.\n\n"
            "Выберите действие:",
            reply_markup=get_bookmarks_menu()
        )
    await callback.answer()

@router.callback_query(F.data == "bookmarks_list")
async def show_bookmarks(callback: CallbackQuery, bot: Bot):
    # 🔑 Проверка подписки
    if not await is_subscribed(bot, callback.from_user.id):
        await callback.answer("🔒 Для доступа к функциям бота подпишитесь на канал @bot_pro_bot_you", show_alert=True)
        return
    
    bookmarks = db.get_bookmarks(callback.from_user.id, limit=20)
    
    if not bookmarks:
        text = "📭 У вас пока нет закладок.\n\nПерешлите любое сообщение мне, чтобы сохранить его!"
        try:
            await callback.message.edit_text(text, reply_markup=get_back_button("bookmarks_menu"))
        except Exception:
            await callback.message.answer(text, reply_markup=get_back_button("bookmarks_menu"))
        return
    
    text = "📌 <b>Ваши закладки</b>:\n\n"
    for i, bm in enumerate(bookmarks[:10], 1):
        content = bm['message_text'][:50] + "..." if bm['message_text'] and len(bm['message_text']) > 50 else bm['message_text']
        text += f"{i}. {content or '📎 Файл/медиа'}\n"
    
    if len(bookmarks) > 10:
        text += f"\n...и ещё {len(bookmarks) - 10} закладок"
    
    try:
        await callback.message.edit_text(text, reply_markup=get_back_button("bookmarks_menu"))
    except Exception:
        await callback.message.answer(text, reply_markup=get_back_button("bookmarks_menu"))
    await callback.answer()

@router.callback_query(F.data == "bookmarks_add")
async def add_bookmark_start(callback: CallbackQuery, state: FSMContext, bot: Bot):
    # 🔑 Проверка подписки
    if not await is_subscribed(bot, callback.from_user.id):
        await callback.answer("🔒 Для доступа к функциям бота подпишитесь на канал @bot_pro_bot_you", show_alert=True)
        return
    
    try:
        await callback.message.edit_text(
            "📤 <b>Добавить закладку</b>\n\n"
            "Перешлите мне любое сообщение, которое хотите сохранить:",
            reply_markup=get_back_button("bookmarks_menu")
        )
    except Exception:
        await callback.message.answer(
            "📤 <b>Добавить закладку</b>\n\n"
            "Перешлите мне любое сообщение, которое хотите сохранить:",
            reply_markup=get_back_button("bookmarks_menu")
        )
    await state.set_state(BookmarkStates.waiting_for_message)
    await callback.answer()

@router.message(BookmarkStates.waiting_for_message)
async def save_bookmark(message: Message, state: FSMContext, bot: Bot):
    # 🔑 Проверка подписки
    if not await is_subscribed(bot, message.from_user.id):
        await message.answer(
            "🔒 <b>Требуется подписка</b>\n\n"
            "Чтобы пользоваться ботом, подпишитесь на наш канал:\n"
            f"<a href='https://t.me/{REQUIRED_CHANNEL.lstrip('@')}'>{REQUIRED_CHANNEL}</a>",
            reply_markup=get_back_button(),
            disable_web_page_preview=True
        )
        if state is not None:
            await state.clear()
        return
    
    # Определяем тип сообщения
    message_type = 'text'
    file_id = None
    
    if message.text:
        message_type = 'text'
        content = message.text
    elif message.photo:
        message_type = 'photo'
        file_id = message.photo[-1].file_id
        content = message.caption or ''
    elif message.document:
        message_type = 'document'
        file_id = message.document.file_id
        content = message.caption or ''
    elif message.video:
        message_type = 'video'
        file_id = message.video.file_id
        content = message.caption or ''
    else:
        content = ''
    
    # Сохраняем в БД
    bookmark_id = db.add_bookmark(
        user_id=message.from_user.id,
        message_text=content,
        message_type=message_type,
        file_id=file_id
    )
    
    # 🔑 ВАЖНО: Проверяем, что state существует перед очисткой
    if state is not None:
        await state.clear()
    
    await message.answer(
        f"✅ <b>Сохранено!</b>\n\n"
        f"Закладка #{bookmark_id} добавлена.\n"
        f"Тип: {message_type}\n\n"
        f"Посмотреть все: /bookmarks",
        reply_markup=get_back_button("bookmarks_menu")
    )

@router.callback_query(F.data == "bookmarks_clear")
async def clear_bookmarks_confirm(callback: CallbackQuery, bot: Bot):
    # 🔑 Проверка подписки
    if not await is_subscribed(bot, callback.from_user.id):
        await callback.answer("🔒 Для доступа к функциям бота подпишитесь на канал @bot_pro_bot_you", show_alert=True)
        return
    
    try:
        await callback.message.edit_text(
            "⚠️ <b>Очистить все закладки?</b>\n\n"
            "Это действие нельзя отменить!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🗑️ Да, очистить", callback_data="bookmarks_clear_confirm")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="bookmarks_menu")]
            ])
        )
    except Exception:
        await callback.message.answer(
            "⚠️ <b>Очистить все закладки?</b>\n\n"
            "Это действие нельзя отменить!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🗑️ Да, очистить", callback_data="bookmarks_clear_confirm")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="bookmarks_menu")]
            ])
        )
    await callback.answer()

@router.callback_query(F.data == "bookmarks_clear_confirm")
async def clear_bookmarks(callback: CallbackQuery, bot: Bot):
    # 🔑 Проверка подписки
    if not await is_subscribed(bot, callback.from_user.id):
        await callback.answer("🔒 Для доступа к функциям бота подпишитесь на канал @bot_pro_bot_you", show_alert=True)
        return
    
    deleted = db.clear_bookmarks(callback.from_user.id)
    text = f"✅ Все закладки удалены ({deleted} шт.)."
    try:
        await callback.message.edit_text(text, reply_markup=get_back_button("bookmarks_menu"))
    except Exception:
        await callback.message.answer(text, reply_markup=get_back_button("bookmarks_menu"))
    await callback.answer()

# 🔑 НОВАЯ ФУНКЦИЯ: Безопасное сохранение из обычного сообщения (без FSM)
async def save_bookmark_simple(message: Message, bot: Bot = None):
    """
    Сохранение закладки без использования FSM.
    Параметр bot используется для проверки подписки.
    """
    # Если бот передан — проверяем подписку
    if bot is not None:
        if not await is_subscribed(bot, message.from_user.id):
            await message.answer(
                "🔒 <b>Требуется подписка</b>\n\n"
                "Чтобы пользоваться ботом, подпишитесь на наш канал:\n"
                f"<a href='https://t.me/{REQUIRED_CHANNEL.lstrip('@')}'>{REQUIRED_CHANNEL}</a>",
                reply_markup=get_back_button(),
                disable_web_page_preview=True
            )
            return
    
    # Определяем тип сообщения
    message_type = 'text'
    file_id = None
    
    if message.text:
        message_type = 'text'
        content = message.text
    elif message.photo:
        message_type = 'photo'
        file_id = message.photo[-1].file_id
        content = message.caption or ''
    elif message.document:
        message_type = 'document'
        file_id = message.document.file_id
        content = message.caption or ''
    elif message.video:
        message_type = 'video'
        file_id = message.video.file_id
        content = message.caption or ''
    else:
        content = ''
    
    # Сохраняем в БД
    bookmark_id = db.add_bookmark(
        user_id=message.from_user.id,
        message_text=content,
        message_type=message_type,
        file_id=file_id
    )
    
    await message.reply(
        f"✅ <b>Сохранено в закладки!</b>\n\nID: #{bookmark_id}",
        reply_markup=get_back_button("bookmarks_menu")
    )
