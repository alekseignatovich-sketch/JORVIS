from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from keyboards import get_notes_menu, get_back_button

router = Router()

# FSM для заметок
class NoteStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_content = State()

@router.callback_query(F.data == "notes_menu")
async def notes_menu(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            "📝 <b>Заметки</b>\n\n"
            "Создавайте быстрые заметки для идей, планов, списков.\n\n"
            "Выберите действие:",
            reply_markup=get_notes_menu()
        )
    except Exception:
        await callback.message.answer(
            "📝 <b>Заметки</b>\n\n"
            "Создавайте быстрые заметки для идей, планов, списков.\n\n"
            "Выберите действие:",
            reply_markup=get_notes_menu()
        )
    await callback.answer()

@router.callback_query(F.data == "notes_list")
async def show_notes(callback: CallbackQuery):
    notes = db.get_notes(callback.from_user.id, limit=20)
    
    if not notes:
        text = "📭 У вас пока нет заметок.\n\nНажмите «✏️ Новая заметка», чтобы создать."
        try:
            await callback.message.edit_text(text, reply_markup=get_back_button("notes_menu"))
        except Exception:
            await callback.message.answer(text, reply_markup=get_back_button("notes_menu"))
        return
    
    text = "📝 <b>Ваши заметки</b>:\n\n"
    for i, note in enumerate(notes[:10], 1):
        title = note['title'][:40] + "..." if len(note['title']) > 40 else note['title']
        text += f"{i}. {title}\n"
    
    if len(notes) > 10:
        text += f"\n...и ещё {len(notes) - 10} заметок"
    
    try:
        await callback.message.edit_text(text, reply_markup=get_back_button("notes_menu"))
    except Exception:
        await callback.message.answer(text, reply_markup=get_back_button("notes_menu"))
    await callback.answer()

@router.callback_query(F.data == "notes_add")
async def add_note_start(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_text(
            "✏️ <b>Новая заметка</b>\n\n"
            "Напишите заголовок заметки:",
            reply_markup=get_back_button("notes_menu")
        )
    except Exception:
        await callback.message.answer(
            "✏️ <b>Новая заметка</b>\n\n"
            "Напишите заголовок заметки:",
            reply_markup=get_back_button("notes_menu")
        )
    await state.set_state(NoteStates.waiting_for_title)
    await callback.answer()

@router.message(NoteStates.waiting_for_title)
async def get_note_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(
        "📄 <b>Содержание</b>\n\n"
        "Напишите текст заметки (или пропустите):",
        reply_markup=get_back_button()
    )
    await state.set_state(NoteStates.waiting_for_content)

@router.message(NoteStates.waiting_for_content)
async def save_note(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data['title']
    content = message.text if message.text else ''
    
    note_id = db.add_note(message.from_user.id, title, content)
    
    # 🔑 ВАЖНО: Проверяем наличие state перед очисткой
    if state is not None:
        await state.clear()
    
    preview = content[:100] + '...' if len(content) > 100 else content
    
    await message.answer(
        f"✅ <b>Заметка создана!</b>\n\n"
        f"📌 {title}\n"
        f"{preview}\n\n"
        f"ID: #{note_id}",
        reply_markup=get_back_button("notes_menu")
    )

# 🔑 НОВАЯ ФУНКЦИЯ: Безопасное отображение заметок через команду
async def show_notes_simple(message: Message):
    """Показать заметки через обычное сообщение (не колбэк)"""
    notes = db.get_notes(message.from_user.id, limit=20)
    
    if not notes:
        text = "📭 У вас пока нет заметок.\n\nНажмите «✏️ Новая заметка» в меню, чтобы создать."
        await message.answer(text, reply_markup=get_back_button("notes_menu"))
        return
    
    text = "📝 <b>Ваши заметки</b>:\n\n"
    for i, note in enumerate(notes[:10], 1):
        title = note['title'][:40] + "..." if len(note['title']) > 40 else note['title']
        text += f"{i}. {title}\n"
    
    if len(notes) > 10:
        text += f"\n...и ещё {len(notes) - 10} заметок"
    
    await message.answer(text, reply_markup=get_back_button("notes_menu"))
