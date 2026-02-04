from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
from ..database import db
from ..keyboards import get_reminders_menu, get_back_button

router = Router()

# FSM для напоминаний
class ReminderStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_time = State()

@router.callback_query(F.data == "reminders_menu")
async def reminders_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "✅ <b>Задачи и напоминания</b>\n\n"
        "Устанавливайте напоминания о важных делах.\n"
        "Пример: <code>напомни завтра в 10 купить молоко</code>\n\n"
        "Выберите действие:",
        reply_markup=get_reminders_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "reminders_list")
async def show_reminders(callback: CallbackQuery):
    reminders = db.get_active_reminders(callback.from_user.id)
    
    if not reminders:
        await callback.message.edit_text(
            "📭 У вас пока нет активных напоминаний.\n\n"
            "Нажмите «➕ Новое напоминание», чтобы создать.",
            reply_markup=get_back_button("reminders_menu")
        )
        return
    
    text = "✅ <b>Ваши напоминания</b>:\n\n"
    for i, rm in enumerate(reminders[:10], 1):
        remind_time = datetime.strptime(rm['remind_at'], '%Y-%m-%d %H:%M:%S')
        text += f"{i}. {rm['text']}\n   🕐 {remind_time.strftime('%d.%m.%Y %H:%M')}\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_back_button("reminders_menu")
    )
    await callback.answer()

@router.callback_query(F.data == "reminders_add")
async def add_reminder_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 <b>Новое напоминание</b>\n\n"
        "Напишите, о чём напомнить:",
        reply_markup=get_back_button("reminders_menu")
    )
    await state.set_state(ReminderStates.waiting_for_text)
    await callback.answer()

@router.message(ReminderStates.waiting_for_text)
async def get_reminder_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer(
        "🕐 <b>Когда напомнить?</b>\n\n"
        "Напишите дату и время в формате:\n"
        "<code>дд.мм.гггг чч:мм</code>\n\n"
        "Или используйте:\n"
        "• <code>сегодня в 18:00</code>\n"
        "• <code>завтра в 9:00</code>\n"
        "• <code>послезавтра в 14:30</code>",
        reply_markup=get_back_button()
    )
    await state.set_state(ReminderStates.waiting_for_time)

@router.message(ReminderStates.waiting_for_time)
async def save_reminder(message: Message, state: FSMContext):
    data = await state.get_data()
    text = data['text']
    time_input = message.text.lower()
    
    # Простой парсер времени (на этапе 2 заменим на ИИ)
    now = datetime.now()
    
    if "сегодня" in time_input:
        base_date = now
        time_input = time_input.replace("сегодня", "").strip()
    elif "завтра" in time_input:
        base_date = now + timedelta(days=1)
        time_input = time_input.replace("завтра", "").strip()
    elif "послезавтра" in time_input:
        base_date = now + timedelta(days=2)
        time_input = time_input.replace("послезавтра", "").strip()
    else:
        # Попытка распарсить дату
        try:
            base_date = datetime.strptime(time_input.split()[0], '%d.%m.%Y')
            time_input = ' '.join(time_input.split()[1:])
        except:
            base_date = now + timedelta(days=1)
    
    # Парсим время
    try:
        time_part = time_input.replace("в", "").replace("часов", "").replace("час", "").strip()
        hour, minute = map(int, time_part.split(':'))
        remind_at = base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    except:
        # По умолчанию — завтра в 9:00
        remind_at = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    
    # Сохраняем
    reminder_id = db.add_reminder(message.from_user.id, text, remind_at)
    
    await message.answer(
        f"✅ <b>Напоминание установлено!</b>\n\n"
        f"📝 {text}\n"
        f"🕐 {remind_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Я напомню вам вовремя!",
        reply_markup=get_back_button("reminders_menu")
    )
    await state.clear()
