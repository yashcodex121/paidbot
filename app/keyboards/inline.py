from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import settings

# Button colours (Bot API 9.4+): "primary" = blue, "success" = green, "danger" = red
PRIMARY, SUCCESS, DANGER = "primary", "success", "danger"


def btn(text: str, style: str | None = None, **kwargs) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, style=style, **kwargs)


def join_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn("📢 Join Channel", PRIMARY, url=settings.force_channel_url)],
        [btn("✅ Verify", SUCCESS, callback_data="verify")],
    ])


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn("🛍️ Shop", SUCCESS, callback_data="shop"),
         btn("🧪 Demo", PRIMARY, callback_data="demo")],
        [btn("💳 Top Up", PRIMARY, callback_data="topup"),
         btn("🎧 Support", DANGER, url=f"https://t.me/{settings.support_username}")],
    ])


def shop_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn(f"💰 Pay Now ₹{settings.product_price}", SUCCESS, callback_data="paynow")],
        [btn("⬅️ Back", PRIMARY, callback_data="menu")],
    ])


def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn("⬅️ Back", PRIMARY, callback_data="menu")],
    ])


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn("❌ Cancel", DANGER, callback_data="cancelpay")],
    ])


def admin_kb(pid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        btn("✅ Approve", SUCCESS, callback_data=f"apv:{pid}"),
        btn("❌ Reject", DANGER, callback_data=f"rej:{pid}"),
    ]])


def broadcast_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        btn("✅ Send Now", SUCCESS, callback_data="bc:yes"),
        btn("❌ Cancel", DANGER, callback_data="bc:no"),
    ]])


# ── TopUp keyboards ────────────────────────────────────────────

TOPUP_AMOUNTS = [49, 99, 199, 499]


def topup_amount_kb() -> InlineKeyboardMarkup:
    styles = [SUCCESS, PRIMARY, SUCCESS, DANGER]
    rows = []
    row = []
    for i, amt in enumerate(TOPUP_AMOUNTS):
        row.append(btn(f"₹{amt}", styles[i], callback_data=f"tu_amt:{amt}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([btn("⬅️ Back", PRIMARY, callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def topup_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn("Cancel TopUp", DANGER, callback_data="tu_cancel")],
    ])


def topup_admin_kb(tid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        btn("Approve", SUCCESS, callback_data=f"tu_apv:{tid}"),
        btn("Reject", DANGER, callback_data=f"tu_rej:{tid}"),
    ]])
