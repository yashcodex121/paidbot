from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from app.config import settings


class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject) -> bool:
        user = getattr(event, "from_user", None)
        return bool(user and user.id in settings.admin_ids)


class IsAdminOrSudo(BaseFilter):
    """True agar user owner/admin hai ya sudo list mein hai."""
    async def __call__(self, event: TelegramObject) -> bool:
        from app.database import sudo  # late import — circular avoid karne ke liye
        user = getattr(event, "from_user", None)
        if not user:
            return False
        if user.id in settings.admin_ids:
            return True
        return await sudo.is_sudo(user.id)
