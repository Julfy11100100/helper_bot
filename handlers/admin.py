import logging
from functools import wraps
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from config.settings import settings
from database.database import Database
from keyboards.admin_kb import (
    get_admin_menu, get_users_menu, get_confirm_keyboard, get_back_keyboard
)
from states.admin_states import AdminStates

logger = logging.getLogger(__name__)
router = Router()
db = Database(settings.DATABASE_URL)


def admin_only(func):
    """Декоратор для проверки прав админа"""
    from functools import wraps

    @wraps(func)
    async def wrapper(callback: CallbackQuery, *args, **kwargs):
        if callback.from_user.id != settings.ADMIN_ID:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        return await func(callback, *args, **kwargs)

    return wrapper


@router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text("Выберите действие:", reply_markup=get_admin_menu())
    await callback.answer()


@router.callback_query(F.data == "manage_users")
async def manage_users_handler(callback: CallbackQuery):
    """Управление пользователями"""
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    await callback.message.edit_text("👥 Управление пользователями:", reply_markup=get_users_menu())
    await callback.answer()


@router.callback_query(F.data == "add_user")
async def add_user_handler(callback: CallbackQuery, state: FSMContext):
    """Добавление пользователя"""
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_user_input)
    await callback.message.edit_text(
        "👤 Добавление пользователя\n\n"
        "Отправьте username (с @) или перешлите сообщение от пользователя:",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_user_input)
async def process_user_input(message: Message, state: FSMContext, bot: Bot):
    """Обработка ввода пользователя"""
    if message.from_user.id != settings.ADMIN_ID:
        return

    user_id = None
    username = None
    first_name = None

    if message.forward_from:
        # Пересланное сообщение
        user_id = message.forward_from.id
        username = message.forward_from.username
        first_name = message.forward_from.first_name
    elif message.text and message.text.startswith('@'):
        # Username
        username = message.text[1:]  # Убираем @
        try:
            # Пытаемся получить информацию о пользователе
            chat = await bot.get_chat(username)
            user_id = chat.id
            first_name = chat.first_name
        except TelegramBadRequest:
            await message.answer("❌ Пользователь не найден или не начинал диалог с ботом")
            return
    else:
        await message.answer("❌ Неверный формат. Отправьте @username или перешлите сообщение")
        return

    # Добавляем пользователя в базу
    success = await db.add_user(user_id, username, first_name)

    if success:
        await message.answer(f"✅ Пользователь {first_name} (@{username}) добавлен!")
    else:
        await message.answer("❌ Ошибка при добавлении пользователя")

    await state.clear()
    await message.answer("Выберите действие:", reply_markup=get_admin_menu())


@router.callback_query(F.data == "list_users")
async def list_users_handler(callback: CallbackQuery):
    """Список пользователей"""
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    users = await db.get_users()

    if not users:
        await callback.message.edit_text("📋 Список пользователей пуст", reply_markup=get_back_keyboard())
    else:
        text = "📋 Список пользователей:\n\n"
        for i, user in enumerate(users, 1):
            username_text = f"@{user.username}" if user.username else "без username"
            text += f"{i}. {user.first_name} ({username_text})\n"

        text += f"\nВсего: {len(users)} пользователей"

        await callback.message.edit_text(text, reply_markup=get_back_keyboard())

    await callback.answer()


@router.callback_query(F.data == "delete_user")
async def delete_user_handler(callback: CallbackQuery, state: FSMContext):
    """Удаление пользователя"""
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    users = await db.get_users()

    if not users:
        await callback.message.edit_text("❌ Нет пользователей для удаления", reply_markup=get_back_keyboard())
        await callback.answer()
        return

    await state.set_state(AdminStates.waiting_for_user_delete)

    text = "❌ Удаление пользователя\n\nВыберите номер пользователя для удаления:\n\n"
    for i, user in enumerate(users, 1):
        username_text = f"@{user.username}" if user.username else "без username"
        text += f"{i}. {user.first_name} ({username_text})\n"

    await callback.message.edit_text(text, reply_markup=get_back_keyboard())
    await callback.answer()


@router.message(AdminStates.waiting_for_user_delete)
async def process_user_delete(message: Message, state: FSMContext):
    """Обработка удаления пользователя"""
    if message.from_user.id != settings.ADMIN_ID:
        return

    try:
        user_index = int(message.text) - 1
        users = await db.get_users()

        if 0 <= user_index < len(users):
            user = users[user_index]
            success = await db.delete_user(user.id)

            if success:
                await message.answer(f"✅ Пользователь {user.first_name} удален!")
            else:
                await message.answer("❌ Ошибка при удалении пользователя")
        else:
            await message.answer("❌ Неверный номер пользователя")

    except ValueError:
        await message.answer("❌ Введите номер пользователя")

    await state.clear()
    await message.answer("Выберите действие:", reply_markup=get_admin_menu())


@router.callback_query(F.data == "set_message")
@admin_only
async def set_message_handler(callback: CallbackQuery, state: FSMContext):
    """Настройка сообщения"""
    await state.set_state(AdminStates.waiting_for_message)

    current_message = await db.get_active_message()
    current_text = ""
    if current_message:
        current_text = f"\n\nТекущее сообщение:\n{current_message.text}"

    await callback.message.edit_text(
        f"💬 Настройка сообщения для рассылки{current_text}\n\n"
        "Отправьте новое сообщение:",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_message)
async def process_message_input(message: Message, state: FSMContext):
    """Обработка ввода сообщения"""
    if message.from_user.id != settings.ADMIN_ID:
        return

    success = await db.save_message(message.text)

    if success:
        await message.answer("✅ Сообщение сохранено!")
    else:
        await message.answer("❌ Ошибка при сохранении сообщения")

    await state.clear()
    await message.answer("Выберите действие:", reply_markup=get_admin_menu())


@router.callback_query(F.data == "broadcast")
@admin_only
async def broadcast_handler(callback: CallbackQuery, state: FSMContext):
    """Рассылка сообщений"""
    message_obj = await db.get_active_message()

    if not message_obj:
        await callback.message.edit_text("❌ Сначала настройте сообщение для рассылки", reply_markup=get_back_keyboard())
        await callback.answer()
        return

    users = await db.get_users()

    if not users:
        await callback.message.edit_text("❌ Нет пользователей для рассылки", reply_markup=get_back_keyboard())
        await callback.answer()
        return

    await state.set_state(AdminStates.confirming_broadcast)

    preview_text = f"📤 Предпросмотр рассылки:\n\n{'-' * 30}\n{message_obj.text}\n{'-' * 30}\n\n"
    preview_text += f"Будет отправлено {len(users)} пользователям.\n\nПродолжить?"

    await callback.message.edit_text(preview_text, reply_markup=get_confirm_keyboard("broadcast"))
    await callback.answer()


@router.callback_query(F.data == "confirm_broadcast")
@admin_only
async def confirm_broadcast_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Подтверждение рассылки"""
    await state.clear()

    message_obj = await db.get_active_message()
    users = await db.get_users()

    await callback.message.edit_text("📤 Начинаю рассылку...", reply_markup=None)

    sent_count = 0
    blocked_count = 0

    for user in users:
        try:
            await bot.send_message(user.id, message_obj.text)
            sent_count += 1
        except TelegramBadRequest as e:
            if "blocked" in str(e).lower():
                blocked_count += 1
                # Деактивируем заблокированного пользователя
                await db.delete_user(user.id)
                logger.info(f"Пользователь {user.id} заблокировал бота")
            else:
                logger.error(f"Ошибка отправки пользователю {user.id}: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке пользователю {user.id}: {e}")

    result_text = f"✅ Рассылка завершена!\n\n"
    result_text += f"📤 Отправлено: {sent_count}\n"
    if blocked_count > 0:
        result_text += f"🚫 Заблокировали бота: {blocked_count}"

    await callback.message.edit_text(result_text, reply_markup=get_admin_menu())
    await callback.answer()


@router.callback_query(F.data == "stats")
@admin_only
async def stats_handler(callback: CallbackQuery):
    """Статистика"""
    stats = await db.get_stats()

    text = "📊 Статистика:\n\n"
    text += f"👥 Активных пользователей: {stats['active_users']}\n"

    if stats['last_message_date']:
        text += f"📅 Последнее сообщение: {stats['last_message_date'].strftime('%d.%m.%Y %H:%M')}"
    else:
        text += "📅 Сообщений еще не было"

    await callback.message.edit_text(text, reply_markup=get_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "export_users")
@admin_only
async def export_users_handler(callback: CallbackQuery):
    """Экспорт списка пользователей"""
    users = await db.get_users()

    if not users:
        await callback.message.edit_text("❌ Нет пользователей для экспорта", reply_markup=get_back_keyboard())
        await callback.answer()
        return

    export_text = "📄 Экспорт пользователей:\n\n"

    for i, user in enumerate(users, 1):
        username_text = f"@{user.username}" if user.username else "без username"
        export_text += f"{i}. {user.first_name} ({username_text}) - ID: {user.id}\n"
        export_text += f"   Добавлен: {user.added_date.strftime('%d.%m.%Y %H:%M')}\n\n"

    export_text += f"Всего пользователей: {len(users)}"

    # Если текст слишком длинный, разбиваем на части
    if len(export_text) > 4000:
        await callback.message.edit_text("📄 Список пользователей (первая часть):")

        parts = [export_text[i:i + 4000] for i in range(0, len(export_text), 4000)]
        for i, part in enumerate(parts):
            if i == 0:
                await callback.message.edit_text(part)
            else:
                await callback.message.answer(part)

        await callback.message.answer("Выберите действие:", reply_markup=get_admin_menu())
    else:
        await callback.message.edit_text(export_text, reply_markup=get_back_keyboard())

    await callback.answer()