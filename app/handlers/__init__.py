from aiogram import Router

from app.handlers import admin, broadcast, menu, payment, start, stats, topup


def get_router() -> Router:
    root = Router(name="root")
    root.include_routers(
        start.router,
        broadcast.router,
        stats.router,
        menu.router,
        payment.router,
        topup.router,
        admin.router,
    )
    return root
