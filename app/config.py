import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _req(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: frozenset[int]
    force_channel_id: int
    force_channel_url: str
    private_channel_id: int
    upi_id: str
    payee_name: str
    admin_log_chat_id: int
    log_channel_id: int | None
    support_username: str
    payment_qr_image: str
    product_price: int
    invite_expiry_seconds: int
    demo_text: str
    db_path: str
    broadcast_delay: float


def load_settings() -> Settings:
    return Settings(
        bot_token=_req("BOT_TOKEN"),
        admin_ids=frozenset(int(x) for x in _req("ADMIN_IDS").split(",") if x.strip()),
        force_channel_id=int(_req("FORCE_CHANNEL_ID")),
        force_channel_url=_req("FORCE_CHANNEL_URL"),
        private_channel_id=int(_req("PRIVATE_CHANNEL_ID")),
        upi_id=_req("UPI_ID"),
        payee_name=_req("PAYEE_NAME"),
        admin_log_chat_id=int(_req("ADMIN_LOG_CHAT_ID")),
        log_channel_id=int(os.getenv("LOG_CHANNEL_ID")) if os.getenv("LOG_CHANNEL_ID") else None,
        support_username=_req("SUPPORT_USERNAME").lstrip("@"),
        payment_qr_image=os.getenv("PAYMENT_QR_IMAGE", "assets/qr.png"),
        product_price=int(os.getenv("PRODUCT_PRICE", "99")),
        invite_expiry_seconds=int(os.getenv("INVITE_EXPIRY_SECONDS", "50")),
        demo_text=os.getenv("DEMO_TEXT", "Demo jaldi add kiya jayega."),
        db_path=os.getenv("DB_PATH", "data/bot.db"),
        broadcast_delay=float(os.getenv("BROADCAST_DELAY", "0.05")),
    )


settings = load_settings()
