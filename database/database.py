import aiosqlite
import logging
from datetime import datetime
from typing import List, Optional
from .models import User, Message

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def init_db(self):
        """Инициализация базы данных и создание таблиц"""
        async with aiosqlite.connect(self.db_path) as db:
            # Создание таблицы пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT NOT NULL,
                    added_date TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Создание таблицы сообщений
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    created_date TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)

            await db.commit()
            logger.info("База данных инициализирована")

    async def add_user(self, user_id: int, username: Optional[str], first_name: str) -> bool:
        """Добавление пользователя"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT OR REPLACE INTO users (id, username, first_name, added_date, is_active) VALUES (?, ?, ?, ?, ?)",
                    (user_id, username, first_name, datetime.now().isoformat(), 1)
                )
                await db.commit()
                logger.info(f"Пользователь {user_id} добавлен")
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя: {e}")
            return False

    async def get_users(self, active_only: bool = True) -> List[User]:
        """Получение списка пользователей"""
        async with aiosqlite.connect(self.db_path) as db:
            query = "SELECT * FROM users"
            if active_only:
                query += " WHERE is_active = 1"

            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [
                    User(
                        id=row[0],
                        username=row[1],
                        first_name=row[2],
                        added_date=datetime.fromisoformat(row[3]),
                        is_active=bool(row[4])
                    )
                    for row in rows
                ]

    async def delete_user(self, user_id: int) -> bool:
        """Мягкое удаление пользователя"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE users SET is_active = 0 WHERE id = ?",
                    (user_id,)
                )
                await db.commit()
                logger.info(f"Пользователь {user_id} деактивирован")
                return True
        except Exception as e:
            logger.error(f"Ошибка удаления пользователя: {e}")
            return False

    async def save_message(self, text: str) -> bool:
        """Сохранение сообщения для рассылки"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Деактивируем все предыдущие сообщения
                await db.execute("UPDATE messages SET is_active = 0")

                # Добавляем новое активное сообщение
                await db.execute(
                    "INSERT INTO messages (text, created_date, is_active) VALUES (?, ?, ?)",
                    (text, datetime.now().isoformat(), 1)
                )
                await db.commit()
                logger.info("Сообщение сохранено")
                return True
        except Exception as e:
            logger.error(f"Ошибка сохранения сообщения: {e}")
            return False

    async def get_active_message(self) -> Optional[Message]:
        """Получение активного сообщения"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT * FROM messages WHERE is_active = 1 ORDER BY created_date DESC LIMIT 1") as cursor:
                row = await cursor.fetchone()
                if row:
                    return Message(
                        id=row[0],
                        text=row[1],
                        created_date=datetime.fromisoformat(row[2]),
                        is_active=bool(row[3])
                    )
                return None

    async def get_stats(self) -> dict:
        """Получение статистики"""
        async with aiosqlite.connect(self.db_path) as db:
            # Количество активных пользователей
            async with db.execute("SELECT COUNT(*) FROM users WHERE is_active = 1") as cursor:
                active_users = (await cursor.fetchone())[0]

            # Последнее сообщение
            message = await self.get_active_message()
            last_message_date = message.created_date if message else None

            return {
                "active_users": active_users,
                "last_message_date": last_message_date
            }