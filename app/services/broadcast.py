import asyncio
import logging
import time

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import Message

from app.config import settings
from app.database import users
from app.services.logger import send_log

log = logging.getLogger(__name__)
_running = False


def is_running() -> bool:
    return _running


async def _copy(bot: Bot, uid: int, src_chat: int, src_msg: int) -> str:
    """Return: 'sent' | 'blocked' | 'failed'"""
    for _ in range(2):
        try:
            await bot.copy_message(uid, src_chat, src_msg)
            return "sent"
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
        except TelegramForbiddenError:
            await users.mark_blocked(uid)
            return "blocked"
        except Exception as e:
            log.info("broadcast to %s failed: %s", uid, e)
            return "failed"
    return "failed"


def _progress_text(done: int, total: int, sent: int, blocked: int, failed: int) -> str:
    return (
        "📢 <b>Broadcast chal raha hai...</b>\n\n"
        f"📊 Progress: <b>{done}/{total}</b>\n"
        f"✅ Sent: {sent}\n🚫 Blocked: {blocked}\n⚠️ Failed: {failed}"
    )


async def run_broadcast(bot: Bot, admin_id: int, src_chat: int, src_msg: int, status: Message) -> None:
    global _running
    _running = True
    started = time.time()
    sent = blocked = failed = 0
    try:
        ids = await users.active_ids()
        total = len(ids)
        for i, uid in enumerate(ids, 1):
            result = await _copy(bot, uid, src_chat, src_msg)
            if result == "sent":
                sent += 1
            elif result == "blocked":
                blocked += 1
            else:
                failed += 1
            await asyncio.sleep(settings.broadcast_delay)
            if i % 50 == 0:
                try:
                    await status.edit_text(_progress_text(i, total, sent, blocked, failed))
                except Exception:
                    pass

        took = int(time.time() - started)
        summary = (
            "✅ <b>Broadcast complete</b>\n\n"
            f"👥 Total: {total}\n✅ Sent: {sent}\n🚫 Blocked: {blocked}\n"
            f"⚠️ Failed: {failed}\n⏱️ Time: {took}s"
        )
        try:
            await status.edit_text(summary)
        except Exception:
            await bot.send_message(admin_id, summary)
        await send_log(bot, f"📢 <b>Broadcast done</b> by <code>{admin_id}</code>\n\n{summary}")
    except Exception as e:
        log.exception("broadcast crashed")
        await bot.send_message(admin_id, f"❌ Broadcast error: <code>{e}</code>")
    finally:
        _running = False
