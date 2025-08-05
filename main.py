import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config.settings import settings
from database.database import Database
from handlers import admin, common

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    # Инициализация бота и диспетчера
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Инициализация базы данных
    db = Database(settings.DATABASE_URL)
    await db.init_db()

    # Регистрация роутеров
    dp.include_router(common.router)
    dp.include_router(admin.router)

    logger.info("Бот запущен")
    # await bot.send_message(settings.ADMIN_ID, "🤖 Бот запущен!")

    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        # await bot.send_message(settings.ADMIN_ID, "🔴 Бот остановлен!")
        logger.info("Бот остановлен")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
