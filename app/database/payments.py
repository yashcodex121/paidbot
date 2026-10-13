import time

from app.database.core import get_db

PENDING, APPROVED, REJECTED = "PENDING", "APPROVED", "REJECTED"


async def create(pid: str, user_id: int, username: str | None, amount: int, file_id: str) -> None:
    db = get_db()
    await db.execute(
        "INSERT INTO payments(id,user_id,username,amount,status,screenshot_file_id,created_at) "
        "VALUES(?,?,?,?,?,?,?)",
        (pid, user_id, username, amount, PENDING, file_id, int(time.time())),
    )
    await db.commit()


async def get(pid: str):
    async with get_db().execute("SELECT * FROM payments WHERE id=?", (pid,)) as cur:
        return await cur.fetchone()


async def user_has_pending(user_id: int) -> bool:
    async with get_db().execute(
        "SELECT 1 FROM payments WHERE user_id=? AND status=? LIMIT 1", (user_id, PENDING)
    ) as cur:
        return await cur.fetchone() is not None


async def decide(pid: str, new_status: str, admin_id: int) -> bool:
    """Atomic: sirf PENDING request approve/reject ho sakti hai (duplicate block)."""
    db = get_db()
    cur = await db.execute(
        "UPDATE payments SET status=?, admin_id=?, decided_at=? WHERE id=? AND status=?",
        (new_status, admin_id, int(time.time()), pid, PENDING),
    )
    await db.commit()
    return cur.rowcount == 1


async def claim_link_slot(pid: str) -> bool:
    """Atomic: ek approved request par sirf ek baar link generate hoga."""
    db = get_db()
    cur = await db.execute(
        "UPDATE payments SET link_issued=1 WHERE id=? AND status=? AND link_issued=0",
        (pid, APPROVED),
    )
    await db.commit()
    return cur.rowcount == 1


async def release_link_slot(pid: str) -> None:
    db = get_db()
    await db.execute("UPDATE payments SET link_issued=0 WHERE id=?", (pid,))
    await db.commit()


async def stats() -> dict:
    """Status-wise count + approved payments ka total revenue."""
    async with get_db().execute(
        "SELECT status, COUNT(*) AS c, COALESCE(SUM(amount),0) AS s FROM payments GROUP BY status"
    ) as cur:
        rows = await cur.fetchall()
    out = {PENDING: 0, APPROVED: 0, REJECTED: 0, "revenue": 0}
    for r in rows:
        out[r["status"]] = r["c"]
        if r["status"] == APPROVED:
            out["revenue"] = r["s"]
    return out
