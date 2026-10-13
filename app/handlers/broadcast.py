import asyncio

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.database import sudo, users
from app.keyboards import broadcast_confirm_kb
from app.services import broadcast as bc
from app.states import BroadcastStates

router = Router(name="broadcast")

_tasks: set[asyncio.Task] = set()


async def _is_allowed(user_id: int) -> bool:
    """Admin ya sudo dono broadcast kar sakte hain."""
    if user_id in settings.admin_ids:
        return True
    return await sudo.is_sudo(user_id)


async def _preview(m: Message, state: FSMContext, source: Message, bot: Bot):
    total, blocked = await users.counts()
    await state.update_data(chat_id=source.chat.id, message_id=source.message_id)
    await state.set_state(BroadcastStates.confirming)
    await bot.copy_message(m.chat.id, source.chat.id, source.message_id)  # preview
    await m.answer(
        "👆 Ye message broadcast hoga.\n\n"
        f"👥 Recipients: <b>{total - blocked}</b> (blocked: {blocked})\n\nConfirm karein?",
        reply_markup=broadcast_confirm_kb(),
    )


@router.message(Command("broadcast"))
async def cmd_broadcast(m: Message, state: FSMContext, bot: Bot):
    if not await _is_allowed(m.from_user.id):
        return  # silently ignore non-admins
    if bc.is_running():
        await m.answer("⏳ Ek broadcast already chal raha hai.")
        return
    if m.reply_to_message:
        await _preview(m, state, m.reply_to_message, bot)
        return
    await state.set_state(BroadcastStates.waiting_message)
    await m.answer(
        "📢 Broadcast message bhejein (text / photo / video / document — kuch bhi).\n"
        "Cancel karne ke liye /cancel"
    )


@router.message(Command("cancel"))
async def cmd_cancel(m: Message, state: FSMContext):
    if not await _is_allowed(m.from_user.id):
        return
    await state.clear()
    await m.answer("❌ Cancelled.")


@router.message(BroadcastStates.waiting_message)
async def got_message(m: Message, state: FSMContext, bot: Bot):
    # state mein sirf allowed users aayenge kyunki /broadcast wahi set karta hai
    await _preview(m, state, m, bot)


@router.callback_query(BroadcastStates.confirming, F.data == "bc:yes")
async def cb_confirm(c: CallbackQuery, state: FSMContext, bot: Bot):
    if not await _is_allowed(c.from_user.id):
        await c.answer("Not allowed.", show_alert=True)
        return
    if bc.is_running():
        await c.answer("Ek broadcast already chal raha hai.", show_alert=True)
        return
    data = await state.get_data()
    await state.clear()
    await c.answer("Started")
    status = await c.message.edit_text("📢 <b>Broadcast start ho raha hai...</b>")
    task = asyncio.create_task(
        bc.run_broadcast(bot, c.from_user.id, data["chat_id"], data["message_id"], status)
    )
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


@router.callback_query(F.data == "bc:no")
async def cb_cancel(c: CallbackQuery, state: FSMContext):
    await state.clear()
    await c.answer("Cancelled")
    await c.message.edit_text("❌ Broadcast cancel kar diya.")
