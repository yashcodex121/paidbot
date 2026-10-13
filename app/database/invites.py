from app.database.core import get_db


async def save(payment_id: str, user_id: int, link: str, expires_at: int) -> int:
    db = get_db()
    cur = await db.execute(
        "INSERT INTO invites(payment_id,user_id,invite_link,expires_at) VALUES(?,?,?,?)",
        (payment_id, user_id, link, expires_at),
    )
    await db.commit()
    return cur.lastrowid


async def mark_revoked(invite_id: int) -> None:
    db = get_db()
    await db.execute("UPDATE invites SET revoked=1 WHERE id=?", (invite_id,))
    await db.commit()


async def list_active():
    async with get_db().execute("SELECT * FROM invites WHERE revoked=0") as cur:
        return await cur.fetchall()
