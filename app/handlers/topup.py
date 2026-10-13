"""
TopUp flow:
  1. User "💳 Top Up" dabata hai  →  amount choose karta hai
  2. UPI details + QR dikhta hai  →  screenshot bhejta hai
  3. Admin log chat mein request jaati hai  →  admin approve/reject karta hai
  4. Approve hone par wallet credit hota hai + user ko notify
  5. /start?start=topup deeplink se bhi seedha aa sakta hai
"""
import html
import secrets

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.database import wallet
from app.keyboards import (
    main_menu_kb,
    topup_admin_kb,
    topup_amount_kb,
    topup_cancel_kb,
)
from app.services.logger import send_log, user_ref
from app.states import TopUpStates

router = Router(name="topup")


# ── helpers ────────────────────────────────────────────────────

async def _is_allowed(user_id: int) -> bool:
    from app.database import sudo
    if user_id in settings.admin_ids:
        return True
    return await sudo.is_sudo(user_id)


async def show_topup_menu(target: Message | CallbackQuery) -> None:
    """Amount selection screen dikhao."""
    balance = await wallet.get_balance(
        target.from_user.id if isinstance(target, Message) else target.from_user.id
    )
    text = (
        "💳 <b>Wallet Top Up</b>\n\n"
        f"💰 Aapka current balance: <b>₹{balance}</b>\n\n"
        "Kitna top up karna chahte hain? Amount choose karein 👇"
    )
    kb = topup_amount_kb()
    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(text, reply_markup=kb)
        except Exception:
            await target.message.answer(text, reply_markup=kb)
    else:
        await target.answer(text, reply_markup=kb)


# ── Amount selection ───────────────────────────────────────────

@router.callback_query(F.data == "topup")
async def cb_topup(c: CallbackQuery, bot: Bot, state: FSMContext):
    from app.services.membership import guard
    if not await guard(c, bot):
        return
    await c.answer()
    await state.clear()
    await show_topup_menu(c)


@router.callback_query(F.data.startswith("tu_amt:"))
async def cb_amount_chosen(c: CallbackQuery, state: FSMContext, bot: Bot):
    from app.services.membership import guard
    if not await guard(c, bot):
        return

    amount = int(c.data.split(":")[1])

    if await wallet.user_has_pending(c.from_user.id):
        await c.answer("⏳ Ek topup request already pending hai.", show_alert=True)
        return

    await state.update_data(topup_amount=amount)
    await state.set_state(TopUpStates.waiting_screenshot)
    await c.answer()

    # Same message edit karo — naya banner nahi banana
    text = (
        f"💳 <b>Top Up ₹{amount}</b>\n\n"
        f"👤 Name: <b>{html.escape(settings.payee_name)}</b>\n"
        f"🆔 UPI ID: <code>{html.escape(settings.upi_id)}</code>\n"
        f"💰 Exact Amount: <b>₹{amount}</b>\n\n"
        "1️⃣ UPI ID par exact amount pay karein.\n"
        "2️⃣ Payment ke baad <b>transaction screenshot</b> yahin bhejein."
    )
    try:
        await c.message.edit_text(text, reply_markup=topup_cancel_kb())
    except Exception:
        await c.message.answer(text, reply_markup=topup_cancel_kb())


# ── Screenshot received ────────────────────────────────────────

@router.message(TopUpStates.waiting_screenshot, F.photo)
async def got_topup_screenshot(m: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    amount = data.get("topup_amount", settings.product_price)

    if await wallet.user_has_pending(m.from_user.id):
        await m.answer("⏳ Aapki topup request already pending hai.")
        await state.clear()
        return

    tid = "TUP-" + secrets.token_hex(4).upper()
    file_id = m.photo[-1].file_id
    uname = m.from_user.username

    await wallet.create_request(tid, m.from_user.id, uname, amount, file_id)
    await state.clear()

    # Admin ko notify karo
    await bot.send_photo(
        settings.admin_log_chat_id,
        file_id,
        caption=(
            "💳 <b>New TopUp Request</b>\n\n"
            f"🆔 Request ID: <code>{tid}</code>\n"
            f"👤 User: <code>{m.from_user.id}</code>"
            + (f" (@{html.escape(uname)})" if uname else "") + "\n"
            f"💰 Amount: <b>₹{amount}</b>\n"
            "📌 Status: <b>PENDING</b>\n\n"
            "UPI history mein verify karke approve karein."
        ),
        reply_markup=topup_admin_kb(tid),
    )
    await send_log(
        bot,
        f"💳 <b>TopUp Request</b> <code>{tid}</code>\n"
        f"{user_ref(m.from_user.id, uname, m.from_user.first_name)}\n"
        f"💰 ₹{amount} • ⏳ PENDING",
    )
    await m.answer(
        f"✅ Screenshot mil gaya!\n"
        f"🆔 Request ID: <code>{tid}</code>\n\n"
        "Admin verify karke aapka wallet credit kar denge.",
        reply_markup=main_menu_kb(),
    )


@router.message(TopUpStates.waiting_screenshot)
async def topup_not_photo(m: Message):
    await m.answer(
        "📸 Kripya payment ka <b>screenshot (photo)</b> bhejein.",
        reply_markup=topup_cancel_kb(),
    )


# ── Cancel ────────────────────────────────────────────────────

@router.callback_query(F.data == "tu_cancel")
async def cb_topup_cancel(c: CallbackQuery, state: FSMContext):
    await state.clear()
    await c.answer("❌ TopUp Cancelled")
    # QR/details message delete karo
    try:
        await c.message.delete()
    except Exception:
        pass
    # Naya reply bhejo
    await c.message.answer("❌ <b>TopUp cancel ho gayi.</b>", reply_markup=main_menu_kb())


# ── Admin: Approve / Reject ────────────────────────────────────

@router.callback_query(F.data.startswith("tu_apv:"))
async def cb_topup_approve(c: CallbackQuery, bot: Bot):
    if not await _is_allowed(c.from_user.id):
        await c.answer("Not allowed.", show_alert=True)
        return

    tid = c.data.split(":", 1)[1]
    if not await wallet.decide(tid, wallet.APPROVED, c.from_user.id):
        await c.answer("Ye request pehle hi process ho chuki hai.", show_alert=True)
        return

    req = await wallet.get_request(tid)
    new_bal = await wallet.credit(req["user_id"], req["amount"])

    # Admin log update
    old_cap = c.message.caption or ""
    try:
        await c.message.edit_caption(
            caption=f"{old_cap}\n\n✅ APPROVED by <code>{c.from_user.id}</code>",
            reply_markup=None,
        )
    except Exception:
        pass

    await c.answer("✅ Approved & wallet credited")

    # User ko notify
    try:
        await bot.send_message(
            req["user_id"],
            f"✅ <b>TopUp Approved!</b>\n\n"
            f"💰 ₹{req['amount']} aapke wallet mein add ho gaye.\n"
            f"💳 New Balance: <b>₹{new_bal}</b>\n\n"
            "Shop se purchase karne ke liye /start dabayein.",
        )
    except Exception:
        pass

    await send_log(
        bot,
        f"✅ <b>TopUp Approved</b> <code>{tid}</code>\n"
        f"User: <code>{req['user_id']}</code> • "
        f"💰 ₹{req['amount']} • New Balance: ₹{new_bal}\n"
        f"By: <code>{c.from_user.id}</code>",
    )


@router.callback_query(F.data.startswith("tu_rej:"))
async def cb_topup_reject(c: CallbackQuery, bot: Bot):
    if not await _is_allowed(c.from_user.id):
        await c.answer("Not allowed.", show_alert=True)
        return

    tid = c.data.split(":", 1)[1]
    if not await wallet.decide(tid, wallet.REJECTED, c.from_user.id):
        await c.answer("Ye request pehle hi process ho chuki hai.", show_alert=True)
        return

    req = await wallet.get_request(tid)

    old_cap = c.message.caption or ""
    try:
        await c.message.edit_caption(
            caption=f"{old_cap}\n\n❌ REJECTED by <code>{c.from_user.id}</code>",
            reply_markup=None,
        )
    except Exception:
        pass

    await c.answer("❌ Rejected")

    try:
        await bot.send_message(
            req["user_id"],
            f"❌ Aapki TopUp request <code>{tid}</code> reject ho gayi.\n"
            "Agar payment hua tha to Support se contact karein.",
        )
    except Exception:
        pass

    await send_log(
        bot,
        f"❌ <b>TopUp Rejected</b> <code>{tid}</code>\n"
        f"User: <code>{req['user_id']}</code> • ₹{req['amount']}\n"
        f"By: <code>{c.from_user.id}</code>",
    )
