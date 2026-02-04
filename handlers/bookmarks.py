from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db  # ← Абсолютный импорт из корня!
from keyboards import get_bookmarks_menu, get_back_button

router = Router()

# FSM для добавления закладки
class BookmarkStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_tags = State()

@router.callback_query(F.data == "bookmarks_menu")
async def bookmarks_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📌 <b>Закладки</b>\n\n"
        "Сохраняйте важные сообщения, ссылки, фото — всё в одном месте.\n\n"
        "Выберите действие:",
        reply_markup=get_bookmarks_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "bookmarks_list")
async def show_bookmarks(callback: CallbackQuery):
    bookmarks = db.get_bookmarks(callback.from_user.id, limit=20)
    
    if not bookmarks:
        await callback.message.edit_text(
            "📭 У вас пока нет закладок.\n\n"
            "Перешлите любое сообщение мне, чтобы сохранить его!",
            reply_markup=get_back_button("bookmarks_menu")
        )
        return
    
    text = "📌 <b>Ваши закладки</b>:\n\n"
    for i, bm in enumerate(bookmarks[:10], 1):  # Показываем первые 10
        content = bm['message_text'][:50] + "..." if bm['message_text'] and len(bm['message_text']) > 50 else bm['message_text']
        text += f"{i}. {content or '📎 Файл/медиа'}\n"
    
    if len(bookmarks) > 10:
        text += f"\n...и ещё {len(bookmarks) - 10} закладок"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_back_button("bookmarks_menu")
    )
    await callback.answer()

@router.callback_query(F.data == "bookmarks_add")
async def add_bookmark_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📤 <b>Добавить закладку</b>\n\n"
        "Перешлите мне любое сообщение, которое хотите сохранить:",
        reply_markup=get_back_button("bookmarks_menu")
    )
    await state.set_state(BookmarkStates.waiting_for_message)
    await callback.answer()

@router.message(BookmarkStates.waiting_for_message)
async def save_bookmark(message: Message, state: FSMContext):
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
    
    await message.answer(
        f"✅ <b>Сохранено!</b>\n\n"
        f"Закладка #{bookmark_id} добавлена.\n"
        f"Тип: {message_type}\n\n"
        f"Посмотреть все: /bookmarks",
        reply_markup=get_back_button("bookmarks_menu")
    )
    await state.clear()

@router.callback_query(F.data == "bookmarks_clear")
async def clear_bookmarks_confirm(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚠️ <b>Очистить все закладки?</b>\n\n"
        "Это действие нельзя отменить!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑️ Да, очистить", callback_data="bookmarks_clear_confirm")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="bookmarks_menu")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data == "bookmarks_clear_confirm")
async def clear_bookmarks(callback: CallbackQuery):
    deleted = db.clear_bookmarks(callback.from_user.id)
    await callback.message.edit_text(
        f"✅ Все закладки удалены ({deleted} шт.).",
        reply_markup=get_back_button("bookmarks_menu")
    )
    await callback.answer()
