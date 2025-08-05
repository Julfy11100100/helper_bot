from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_menu() -> InlineKeyboardMarkup:
    """Главное меню админа"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Управление пользователями", callback_data="manage_users")],
        [InlineKeyboardButton(text="💬 Настройка сообщения", callback_data="set_message")],
        [InlineKeyboardButton(text="📤 Отправить всем", callback_data="broadcast")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")]
    ])
    return keyboard

def get_users_menu() -> InlineKeyboardMarkup:
    """Меню управления пользователями"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить пользователя", callback_data="add_user")],
        [InlineKeyboardButton(text="❌ Удалить пользователя", callback_data="delete_user")],
        [InlineKeyboardButton(text="📋 Список пользователей", callback_data="list_users")],
        [InlineKeyboardButton(text="📄 Экспорт списка", callback_data="export_users")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ])
    return keyboard

def get_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}"),
            InlineKeyboardButton(text="❌ Нет", callback_data="main_menu")
        ]
    ])
    return keyboard

def get_back_keyboard() -> InlineKeyboardMarkup:
    """Кнопка назад"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ])
    return keyboard