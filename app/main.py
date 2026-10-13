import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app import database
from app.config import settings
from app.handlers import get_router
from app.services.invite_service import recover_expiry_tasks
from app.services.logger import send_log


async def run() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    await database.init_db(settings.db_path)

    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(get_router())

    await recover_expiry_tasks(bot)
    await send_log(bot, "🟢 <b>Bot started</b>")
    try:
        await dp.start_polling(bot)
    finally:
        await send_log(bot, "🔴 <b>Bot stopped</b>")
        await database.close_db()
        await bot.session.close()
