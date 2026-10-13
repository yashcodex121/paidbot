import html

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.config import settings
from app.keyboards import back_kb, shop_kb
from app.services.membership import guard, is_member, show_menu

router = Router(name="menu")


@router.callback_query(F.data == "menu")
async def cb_menu(c: CallbackQuery, bot: Bot, state: FSMContext):
    await state.clear()
    if not await is_member(bot, c.from_user.id):
        await c.answer("Pehle channel join karein.", show_alert=True)
        return
    await c.answer()
    await show_menu(c)


@router.callback_query(F.data == "shop")
async def cb_shop(c: CallbackQuery, bot: Bot):
    if not await guard(c, bot):
        return
    await c.answer()
    await c.message.edit_text(
        "🛍️ <b>Shop</b>\n\n"
        "🔐 <b>Private Channel Access</b>\n"
        f"💰 Price: <b>₹{settings.product_price}</b>\n\n"
        "Payment verify hone ke baad aapko single-use invite link milega.",
        reply_markup=shop_kb(),
    )


@router.callback_query(F.data == "demo")
async def cb_demo(c: CallbackQuery, bot: Bot):
    if not await guard(c, bot):
        return
    await c.answer()
    await c.message.edit_text(
        f"🧪 <b>Demo</b>\n\n{html.escape(settings.demo_text)}", reply_markup=back_kb()
    )
