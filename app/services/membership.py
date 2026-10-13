import logging

from aiogram import Bot
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.keyboards import join_kb, main_menu_kb

log = logging.getLogger(__name__)


async def is_member(bot: Bot, user_id: int) -> bool:
    try:
        m = await bot.get_chat_member(settings.force_channel_id, user_id)
    except Exception as e:
        log.warning("membership check failed: %s", e)
        return False
    if m.status in ("member", "administrator", "creator"):
        return True
    return m.status == "restricted" and getattr(m, "is_member", False)


async def guard(c: CallbackQuery, bot: Bot) -> bool:
    """True agar user force channel ka member hai, warna join prompt dikhata hai."""
    if await is_member(bot, c.from_user.id):
        return True
    await c.answer("Pehle channel join karein.", show_alert=True)
    await c.message.answer("Channel join karke Verify dabayein 👇", reply_markup=join_kb())
    return False


async def show_menu(target: Message | CallbackQuery) -> None:
    text = "🏠 <b>Main Menu</b>\nNeeche se option chuniye 👇"
    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(text, reply_markup=main_menu_kb())
        except Exception:
            await target.message.answer(text, reply_markup=main_menu_kb())
    else:
        await target.answer(text, reply_markup=main_menu_kb())
