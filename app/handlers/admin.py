import html
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.database import payments, sudo
from app.services.invite_service import issue_invite
from app.services.logger import send_log, user_ref

log = logging.getLogger(__name__)
router = Router(name="admin")


# ──────────────────────────────────────────────────────────────
# /addsudo  — sirf owner/admin use kar sakta hai
# ──────────────────────────────────────────────────────────────
@router.message(Command("addsudo"))
async def cmd_add_sudo(m: Message):
    # Admin check — agar fail ho toh seedha bata do
    if m.from_user.id not in settings.admin_ids:
        await m.answer("⛔ Ye command sirf bot owner ke liye hai.")
        return

    target_id: int | None = None
    target_username: str | None = None

    # Case 1: reply to a message
    if m.reply_to_message and m.reply_to_message.from_user:
        u = m.reply_to_message.from_user
        target_id = u.id
        target_username = u.username
    else:
        args = (m.text or "").split(maxsplit=1)
        if len(args) < 2:
            await m.answer(
                "❓ <b>Usage:</b>\n"
                "<code>/addsudo 123456789</code>\n"
                "ya kisi message par reply karke <code>/addsudo</code>"
            )
            return
        arg = args[1].strip().lstrip("@")
        if arg.isdigit():
            target_id = int(arg)
        else:
            await m.answer(
                "⚠️ Sirf numeric user ID support hai.\n"
                "Example: <code>/addsudo 123456789</code>\n"
                "Ya user ke message par reply karke /addsudo bhejein."
            )
            return

    if target_id in settings.admin_ids:
        await m.answer("ℹ️ Ye user pehle se hi owner/admin hai.")
        return

    added = await sudo.add(target_id, target_username, m.from_user.id)
    if not added:
        await m.answer(f"ℹ️ <code>{target_id}</code> pehle se sudo list mein hai.")
        return

    uname = f"@{target_username}" if target_username else f"<code>{target_id}</code>"
    await m.answer(
        f"✅ <b>Sudo add ho gaya!</b>\n"
        f"👤 User: {uname}\n"
        f"🔑 Ab ye payment approve/reject kar sakta hai aur broadcast bhej sakta hai."
    )
    await send_log(
        m.bot,
        f"🔑 <b>Sudo Added</b>\n"
        f"User: {uname} (<code>{target_id}</code>)\n"
        f"By: <code>{m.from_user.id}</code>",
    )


# ──────────────────────────────────────────────────────────────
# /removesudo  — sirf owner/admin use kar sakta hai
# ──────────────────────────────────────────────────────────────
@router.message(Command("removesudo"))
async def cmd_remove_sudo(m: Message):
    if m.from_user.id not in settings.admin_ids:
        await m.answer("⛔ Ye command sirf bot owner ke liye hai.")
        return

    target_id: int | None = None
    target_username: str | None = None

    if m.reply_to_message and m.reply_to_message.from_user:
        u = m.reply_to_message.from_user
        target_id = u.id
        target_username = u.username
    else:
        args = (m.text or "").split(maxsplit=1)
        if len(args) < 2 or not args[1].strip().isdigit():
            await m.answer(
                "❓ <b>Usage:</b>\n"
                "<code>/removesudo 123456789</code>\n"
                "ya message par reply karke <code>/removesudo</code>"
            )
            return
        target_id = int(args[1].strip())

    removed = await sudo.remove(target_id)
    uname = f"@{target_username}" if target_username else f"<code>{target_id}</code>"
    if not removed:
        await m.answer(f"⚠️ {uname} sudo list mein nahi tha.")
        return

    await m.answer(f"✅ {uname} sudo list se hata diya gaya.")
    await send_log(
        m.bot,
        f"🗑️ <b>Sudo Removed</b>\n"
        f"User: {uname} (<code>{target_id}</code>)\n"
        f"By: <code>{m.from_user.id}</code>",
    )


# ──────────────────────────────────────────────────────────────
# /sudolist  — saare sudo users dekhein
# ──────────────────────────────────────────────────────────────
@router.message(Command("sudolist"))
async def cmd_sudo_list(m: Message):
    if m.from_user.id not in settings.admin_ids:
        await m.answer("⛔ Ye command sirf bot owner ke liye hai.")
        return

    sudos = await sudo.all_sudos()
    if not sudos:
        await m.answer("📋 Abhi koi sudo user nahi hai.")
        return
    lines = ["📋 <b>Sudo Users:</b>\n"]
    for s in sudos:
        uname = f"@{s['username']}" if s["username"] else f"<code>{s['user_id']}</code>"
        lines.append(f"• {uname} (ID: <code>{s['user_id']}</code>) — added by <code>{s['added_by']}</code>")
    await m.answer("\n".join(lines))


# ──────────────────────────────────────────────────────────────
# Internal helper — admin ya sudo dono allowed
# ──────────────────────────────────────────────────────────────
async def _is_allowed(user_id: int) -> bool:
    if user_id in settings.admin_ids:
        return True
    return await sudo.is_sudo(user_id)


async def _mark_log(c: CallbackQuery, status: str) -> None:
    base = (c.message.caption or "").replace("Status: PENDING", f"Status: {status}")
    icon = "✅" if status == payments.APPROVED else "❌"
    try:
        await c.message.edit_caption(
            caption=f"{base}\n\n{icon} {status} by <code>{c.from_user.id}</code>",
            reply_markup=None,
        )
    except Exception as e:
        log.warning("edit log failed: %s", e)


@router.callback_query(F.data.startswith("rej:"))
async def cb_reject(c: CallbackQuery, bot: Bot):
    if not await _is_allowed(c.from_user.id):
        await c.answer("Not allowed.", show_alert=True)
        return
    pid = c.data.split(":", 1)[1]
    if not await payments.decide(pid, payments.REJECTED, c.from_user.id):
        await c.answer("Ye request pehle hi process ho chuki hai.", show_alert=True)
        return
    p = await payments.get(pid)
    await c.answer("Rejected")
    await _mark_log(c, payments.REJECTED)
    await send_log(
        bot,
        f"❌ <b>Payment Rejected</b> <code>{pid}</code>\n"
        f"{user_ref(p['user_id'], p['username'])}\n👮 By: <code>{c.from_user.id}</code>",
    )
    try:
        await bot.send_message(
            p["user_id"],
            f"❌ Aapki payment request <code>{pid}</code> reject ho gayi.\n"
            "Agar payment ho chuki hai to Support se contact karein.",
        )
    except Exception as e:
        log.warning("notify user failed: %s", e)


@router.callback_query(F.data.startswith("apv:"))
async def cb_approve(c: CallbackQuery, bot: Bot):
    if not await _is_allowed(c.from_user.id):
        await c.answer("Not allowed.", show_alert=True)
        return
    pid = c.data.split(":", 1)[1]
    if not await payments.decide(pid, payments.APPROVED, c.from_user.id):
        await c.answer("Ye request pehle hi process ho chuki hai.", show_alert=True)
        return
    await _mark_log(c, payments.APPROVED)

    if not await payments.claim_link_slot(pid):
        await c.answer("Link already issued.", show_alert=True)
        return

    p = await payments.get(pid)
    try:
        link = await issue_invite(bot, pid, p["user_id"])
        await bot.send_message(
            p["user_id"],
            "✅ <b>Payment Approved!</b>\n\n"
            f"🔗 Aapka private channel link:\n{link}\n\n"
            f"⏱️ Ye link sirf <b>{settings.invite_expiry_seconds} seconds</b> valid hai "
            "aur sirf <b>1 baar</b> use ho sakta hai. Abhi join karein!",
        )
        await c.answer("Approved & link sent")
        await send_log(
            bot,
            f"✅ <b>Payment Approved</b> <code>{pid}</code>\n"
            f"{user_ref(p['user_id'], p['username'])}\n"
            f"💰 ₹{p['amount']} • 👮 By: <code>{c.from_user.id}</code>\n"
            f"🔗 Invite issued ({settings.invite_expiry_seconds}s, single-use)",
        )
    except Exception as e:
        log.exception("link creation failed")
        await payments.release_link_slot(pid)
        await send_log(bot, f"⚠️ <b>Invite link failed</b> <code>{pid}</code>\n<code>{html.escape(str(e))}</code>")
        await c.message.answer(
            f"⚠️ {pid}: link generate/send nahi hua: <code>{html.escape(str(e))}</code>\n"
            "Bot ko private channel mein admin (Invite Users permission) banayein."
        )
