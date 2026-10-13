"""Log channel: bot ke important events ek Telegram channel mein bhejta hai."""
import html
import logging

from aiogram import Bot
from aiogram.types import LinkPreviewOptions

from app.config import settings

log = logging.getLogger(__name__)


def user_ref(user_id: int, username: str | None = None, name: str | None = None) -> str:
    label = f"@{username}" if username else (name or str(user_id))
    return f'<a href="tg://user?id={user_id}">{html.escape(label)}</a> (<code>{user_id}</code>)'


async def send_log(bot: Bot, text: str) -> None:
    """LOG_CHANNEL_ID set nahi hai to silently skip. Kabhi exception raise nahi karta."""
    if not settings.log_channel_id:
        return
    try:
        await bot.send_message(
            settings.log_channel_id,
            text,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
    except Exception as e:
        log.warning("log channel send failed: %s", e)
