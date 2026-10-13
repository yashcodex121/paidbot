import asyncio
import logging
import time

from aiogram import Bot

from app.config import settings
from app.database import invites
from app.services.logger import send_log

log = logging.getLogger(__name__)
_tasks: set[asyncio.Task] = set()


def _spawn(coro) -> None:
    task = asyncio.create_task(coro)
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


async def _expire(bot: Bot, invite_id: int, link: str, expires_at: int) -> None:
    await asyncio.sleep(max(0, expires_at - time.time()))
    try:
        await bot.revoke_chat_invite_link(settings.private_channel_id, link)
    except Exception as e:  # already used / expired / revoked
        log.info("revoke note (%s): %s", link, e)
    await invites.mark_revoked(invite_id)
    log.info("invite %s revoked", invite_id)
    await send_log(bot, f"🔒 <b>Invite revoked</b> (#{invite_id}) — expiry complete")


async def issue_invite(bot: Bot, payment_id: str, user_id: int) -> str:
    """Single-use link banata hai, DB mein save karta hai aur auto-revoke schedule karta hai."""
    expires_at = int(time.time()) + settings.invite_expiry_seconds
    link = await bot.create_chat_invite_link(
        settings.private_channel_id,
        name=payment_id,
        member_limit=1,
        expire_date=expires_at,
    )
    invite_id = await invites.save(payment_id, user_id, link.invite_link, expires_at)
    _spawn(_expire(bot, invite_id, link.invite_link, expires_at))
    return link.invite_link


async def recover_expiry_tasks(bot: Bot) -> None:
    rows = await invites.list_active()
    for r in rows:
        _spawn(_expire(bot, r["id"], r["invite_link"], r["expires_at"]))
    log.info("recovered %d pending expiry tasks", len(rows))
