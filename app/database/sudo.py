import time

from app.database.core import get_db


async def add(user_id: int, username: str | None, added_by: int) -> bool:
    """Sudo add karta hai. True agar naya tha, False agar pehle se tha."""
    db = get_db()
    async with db.execute("SELECT 1 FROM sudos WHERE user_id=?", (user_id,)) as cur:
        if await cur.fetchone():
            return False
    await db.execute(
        "INSERT INTO sudos(user_id, username, added_by, added_at) VALUES(?,?,?,?)",
        (user_id, username, added_by, int(time.time())),
    )
    await db.commit()
    return True


async def remove(user_id: int) -> bool:
    """Sudo remove karta hai. True agar mila aur delete hua."""
    db = get_db()
    async with db.execute("SELECT 1 FROM sudos WHERE user_id=?", (user_id,)) as cur:
        if not await cur.fetchone():
            return False
    await db.execute("DELETE FROM sudos WHERE user_id=?", (user_id,))
    await db.commit()
    return True


async def is_sudo(user_id: int) -> bool:
    """Check karta hai ki user sudo hai ya nahi."""
    async with get_db().execute(
        "SELECT 1 FROM sudos WHERE user_id=?", (user_id,)
    ) as cur:
        return await cur.fetchone() is not None


async def all_sudos() -> list[dict]:
    """Saare sudo users ki list return karta hai."""
    async with get_db().execute(
        "SELECT user_id, username, added_by, added_at FROM sudos ORDER BY added_at"
    ) as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]
