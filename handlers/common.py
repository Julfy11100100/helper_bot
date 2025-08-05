from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from config.settings import settings

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message):
    """Обработка команды /start"""
    if message.from_user.id == settings.ADMIN_ID:
        await message.answer("🔧 Добро пожаловать в админ-панель!")
        # Импортируем здесь чтобы избежать циклических импортов
        from keyboards.admin_kb import get_admin_menu
        await message.answer("Выберите действие:", reply_markup=get_admin_menu())
    else:
        await message.answer("❌ У вас нет доступа к этому боту.")
