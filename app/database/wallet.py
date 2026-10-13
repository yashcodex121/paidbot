import time

from app.database.core import get_db

PENDING, APPROVED, REJECTED = "PENDING", "APPROVED", "REJECTED"


# ── Wallet balance ─────────────────────────────────────────────

async def get_balance(user_id: int) -> int:
    async with get_db().execute(
        "SELECT balance FROM wallets WHERE user_id=?", (user_id,)
    ) as cur:
        row = await cur.fetchone()
    return row["balance"] if row else 0


async def credit(user_id: int, amount: int) -> int:
    """Balance add karo, naya balance return karo."""
    db = get_db()
    await db.execute(
        "INSERT INTO wallets(user_id, balance) VALUES(?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET balance=balance+?",
        (user_id, amount, amount),
    )
    await db.commit()
    return await get_balance(user_id)


async def debit(user_id: int, amount: int) -> bool:
    """Balance katao. True agar successful, False agar balance kam tha."""
    db = get_db()
    cur = await db.execute(
        "UPDATE wallets SET balance=balance-? WHERE user_id=? AND balance>=?",
        (amount, user_id, amount),
    )
    await db.commit()
    return cur.rowcount == 1


# ── TopUp requests ─────────────────────────────────────────────

async def create_request(tid: str, user_id: int, username: str | None,
                         amount: int, file_id: str) -> None:
    db = get_db()
    await db.execute(
        "INSERT INTO topup_requests(id,user_id,username,amount,status,screenshot_file_id,created_at)"
        " VALUES(?,?,?,?,?,?,?)",
        (tid, user_id, username, amount, PENDING, file_id, int(time.time())),
    )
    await db.commit()


async def get_request(tid: str):
    async with get_db().execute(
        "SELECT * FROM topup_requests WHERE id=?", (tid,)
    ) as cur:
        return await cur.fetchone()


async def user_has_pending(user_id: int) -> bool:
    async with get_db().execute(
        "SELECT 1 FROM topup_requests WHERE user_id=? AND status=? LIMIT 1",
        (user_id, PENDING),
    ) as cur:
        return await cur.fetchone() is not None


async def decide(tid: str, new_status: str, admin_id: int) -> bool:
    """Sirf PENDING request change ho sakti hai. True agar update hua."""
    db = get_db()
    cur = await db.execute(
        "UPDATE topup_requests SET status=?, admin_id=?, decided_at=? WHERE id=? AND status=?",
        (new_status, admin_id, int(time.time()), tid, PENDING),
    )
    await db.commit()
    return cur.rowcount == 1
