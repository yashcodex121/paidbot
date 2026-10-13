import html

from aiogram import Bot, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, MessageEntity

from app.config import settings
from app.database import users
from app.keyboards import join_kb, main_menu_kb
from app.services.logger import send_log, user_ref
from app.services.membership import is_member

router = Router(name="start")


def _welcome_msg(first_name: str, price: int) -> tuple[str, list[MessageEntity]]:
    name = first_name

    text = (
        f"𓆩 WELCOME, {name} 𓆪\n\n"
        f"💎 PREMIUM ACCESS | \u20b9{price}\n\n"
        f"🔐 Join the channel & verify yourself.\n"
        f"⚡ Explore, pay & unlock your access!\n\n"
        f"🚀 YOUR JOURNEY STARTS HERE"
    )

    def u16off(sub: str) -> int:
        idx = text.index(sub)
        return len(text[:idx].encode("utf-16-le")) // 2

    def u16len(s: str) -> int:
        return len(s.encode("utf-16-le")) // 2

    welcome_str = f"WELCOME, {name}"
    premium_str = f"PREMIUM ACCESS | \u20b9{price}"

    entities = [
        MessageEntity(type="bold",
                      offset=u16off("WELCOME"),
                      length=u16len(welcome_str)),
        MessageEntity(type="bold",
                      offset=u16off("PREMIUM ACCESS"),
                      length=u16len(premium_str)),
        MessageEntity(type="bold",
                      offset=u16off("YOUR JOURNEY"),
                      length=u16len("YOUR JOURNEY STARTS HERE")),
    ]
    return text, entities


@router.message(CommandStart())
async def cmd_start(m: Message, bot: Bot, state: FSMContext):
    await state.clear()
    u = m.from_user

    is_new = await users.upsert(u.id, u.username, u.first_name)
    if is_new:
        await send_log(bot, f"🆕 <b>New User</b>\n{user_ref(u.id, u.username, u.first_name)}")

    payload = m.text.split(maxsplit=1)[1] if len(m.text.split()) > 1 else ""

    if not await is_member(bot, u.id):
        if payload:
            await state.update_data(start_payload=payload)
        # Simple join banner — pehle jaisa
        await m.answer(
            f"👋 Welcome <b>{html.escape(u.first_name)}</b>!\n\n"
            "Bot use karne ke liye pehle hamara channel join karein, "
            "phir <b>Verify</b> dabayein.",
            reply_markup=join_kb(),
        )
        return

    if payload == "topup":
        from app.handlers.topup import show_topup_menu
        await show_topup_menu(m)
        return

    # Welcome message with custom emoji (no parse_mode — entities use kar rahe hain)
    text, entities = _welcome_msg(u.first_name, settings.product_price)
    await m.answer(
        text,
        entities=entities,
        parse_mode=None,
        reply_markup=main_menu_kb(),
    )


@router.callback_query(F.data == "verify")
async def cb_verify(c: CallbackQuery, bot: Bot, state: FSMContext):
    if not await is_member(bot, c.from_user.id):
        await c.answer("❌ Aapne abhi channel join nahi kiya.", show_alert=True)
        return

    await c.answer("✅ Verified!")

    data = await state.get_data()
    payload = data.get("start_payload", "")
    await state.clear()

    if payload == "topup":
        from app.handlers.topup import show_topup_menu
        await show_topup_menu(c)
        return

    u = c.from_user
    text, entities = _welcome_msg(u.first_name, settings.product_price)
    try:
        await c.message.edit_text(
            text,
            entities=entities,
            parse_mode=None,
            reply_markup=main_menu_kb(),
        )
    except Exception:
        await c.message.answer(
            text,
            entities=entities,
            parse_mode=None,
            reply_markup=main_menu_kb(),
        )
