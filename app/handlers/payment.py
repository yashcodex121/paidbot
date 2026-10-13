import html
import secrets

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.database import payments
from app.keyboards import admin_kb, cancel_kb, main_menu_kb
from app.services.logger import send_log, user_ref
from app.services.membership import guard
from app.states import PayStates

router = Router(name="payment")


@router.callback_query(F.data == "paynow")
async def cb_paynow(c: CallbackQuery, bot: Bot, state: FSMContext):
    if not await guard(c, bot):
        return
    if await payments.user_has_pending(c.from_user.id):
        await c.answer("⏳ Aapki ek payment request already pending hai.", show_alert=True)
        return
    await c.answer()

    text = (
        "💳 <b>UPI Payment</b>\n\n"
        f"👤 Name: <b>{html.escape(settings.payee_name)}</b>\n"
        f"🆔 UPI ID: <code>{html.escape(settings.upi_id)}</code>\n"
        f"💰 Exact Amount: <b>₹{settings.product_price}</b>\n\n"
        "1️⃣ UPI ID par exact amount pay karein.\n"
        "2️⃣ Payment ke baad <b>transaction screenshot</b> yahin bhejein."
    )
    # Same message edit karo — naya banner nahi banana
    try:
        await c.message.edit_text(text, reply_markup=cancel_kb())
    except Exception:
        await c.message.answer(text, reply_markup=cancel_kb())

    await state.set_state(PayStates.waiting_screenshot)


@router.callback_query(F.data == "cancelpay")
async def cb_cancel(c: CallbackQuery, state: FSMContext):
    await state.clear()
    await c.answer("❌ Cancelled")
    # Message delete karo aur naya reply do
    try:
        await c.message.delete()
    except Exception:
        pass
    await c.message.answer("❌ <b>Payment cancel ho gayi.</b>", reply_markup=main_menu_kb())


@router.message(PayStates.waiting_screenshot, F.photo)
async def got_screenshot(m: Message, bot: Bot, state: FSMContext):
    if await payments.user_has_pending(m.from_user.id):
        await m.answer("⏳ Aapki request already pending hai.")
        await state.clear()
        return

    pid = "PAY-" + secrets.token_hex(4).upper()
    file_id = m.photo[-1].file_id
    uname = m.from_user.username
    await payments.create(pid, m.from_user.id, uname, settings.product_price, file_id)
    await state.clear()

    await bot.send_photo(
        settings.admin_log_chat_id,
        file_id,
        caption=(
            "🧾 <b>New Payment Request</b>\n\n"
            f"🆔 Request ID: <code>{pid}</code>\n"
            f"👤 User ID: <code>{m.from_user.id}</code>\n"
            f"🔖 Username: {('@' + html.escape(uname)) if uname else 'N/A'}\n"
            f"💰 Amount: <b>₹{settings.product_price}</b>\n"
            "📌 Status: <b>PENDING</b>\n\n"
            "Screenshot upar attach hai — verify karke approve karein."
        ),
        reply_markup=admin_kb(pid),
    )
    await send_log(
        bot,
        f"🧾 <b>Payment Request</b> <code>{pid}</code>\n"
        f"{user_ref(m.from_user.id, uname, m.from_user.first_name)}\n"
        f"💰 ₹{settings.product_price} • ⏳ PENDING",
    )
    await m.answer(
        f"✅ Screenshot mil gaya!\n🆔 Request ID: <code>{pid}</code>\n\n"
        "Admin verification ke baad aapko link bhej diya jayega.",
        reply_markup=main_menu_kb(),
    )


@router.message(PayStates.waiting_screenshot)
async def not_photo(m: Message):
    await m.answer(
        "📸 Kripya payment ka <b>screenshot (photo)</b> bhejein.", reply_markup=cancel_kb()
    )
