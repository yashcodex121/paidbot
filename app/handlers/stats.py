from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database import payments, users
from app.filters import IsAdmin

router = Router(name="stats")
router.message.filter(IsAdmin())


@router.message(Command("stats"))
async def cmd_stats(m: Message):
    total, blocked = await users.counts()
    s = await payments.stats()
    await m.answer(
        "📊 <b>Bot Stats</b>\n\n"
        f"👥 Users: <b>{total}</b> (blocked: {blocked})\n\n"
        f"⏳ Pending: {s[payments.PENDING]}\n"
        f"✅ Approved: {s[payments.APPROVED]}\n"
        f"❌ Rejected: {s[payments.REJECTED]}\n"
        f"💰 Revenue: <b>₹{s['revenue']}</b>"
    )
