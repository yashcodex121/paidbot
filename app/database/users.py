import time

from app.database.core import get_db


async def upsert(user_id: int, username: str | None, first_name: str | None) -> bool:
    """User save/update karta hai. True return karta hai agar user naya tha."""
    db = get_db()
    async with db.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)) as cur:
        exists = await cur.fetchone() is not None
    await db.execute(
        "INSERT INTO users(user_id,username,first_name,created_at) VALUES(?,?,?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, "
        "first_name=excluded.first_name, is_blocked=0",
        (user_id, username, first_name, int(time.time())),
    )
    await db.commit()
    return not exists


async def active_ids() -> list[int]:
    async with get_db().execute("SELECT user_id FROM users WHERE is_blocked=0") as cur:
        return [r["user_id"] for r in await cur.fetchall()]


async def mark_blocked(user_id: int) -> None:
    db = get_db()
    await db.execute("UPDATE users SET is_blocked=1 WHERE user_id=?", (user_id,))
    await db.commit()


async def counts() -> tuple[int, int]:
    """(total, blocked)"""
    async with get_db().execute(
        "SELECT COUNT(*) AS t, COALESCE(SUM(is_blocked),0) AS b FROM users"
    ) as cur:
        r = await cur.fetchone()
    return r["t"], r["b"]
