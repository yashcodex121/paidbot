import os

import aiosqlite

_conn: aiosqlite.Connection | None = None

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    is_blocked INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER
);
CREATE TABLE IF NOT EXISTS payments(
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    username TEXT,
    amount INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    screenshot_file_id TEXT,
    admin_id INTEGER,
    link_issued INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER,
    decided_at INTEGER
);
CREATE TABLE IF NOT EXISTS invites(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    invite_link TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    revoked INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS sudos(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    added_by INTEGER NOT NULL,
    added_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS wallets(
    user_id INTEGER PRIMARY KEY,
    balance INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS topup_requests(
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    username TEXT,
    amount INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    screenshot_file_id TEXT,
    admin_id INTEGER,
    created_at INTEGER,
    decided_at INTEGER
);
"""


async def init_db(path: str) -> None:
    global _conn
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    _conn = await aiosqlite.connect(path)
    _conn.row_factory = aiosqlite.Row
    await _conn.executescript(SCHEMA)
    # migration: purane DB mein is_blocked column add karo
    async with _conn.execute("PRAGMA table_info(users)") as cur:
        cols = [r["name"] for r in await cur.fetchall()]
    if "is_blocked" not in cols:
        await _conn.execute("ALTER TABLE users ADD COLUMN is_blocked INTEGER NOT NULL DEFAULT 0")
    # migration: sudos table
    async with _conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='sudos'"
    ) as cur:
        if not await cur.fetchone():
            await _conn.execute(
                "CREATE TABLE sudos("
                "user_id INTEGER PRIMARY KEY,"
                "username TEXT,"
                "added_by INTEGER NOT NULL,"
                "added_at INTEGER NOT NULL)"
            )
    # migration: wallets table
    async with _conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='wallets'"
    ) as cur:
        if not await cur.fetchone():
            await _conn.execute(
                "CREATE TABLE wallets(user_id INTEGER PRIMARY KEY, balance INTEGER NOT NULL DEFAULT 0)"
            )
    # migration: topup_requests table
    async with _conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='topup_requests'"
    ) as cur:
        if not await cur.fetchone():
            await _conn.execute(
                "CREATE TABLE topup_requests("
                "id TEXT PRIMARY KEY,"
                "user_id INTEGER NOT NULL,"
                "username TEXT,"
                "amount INTEGER NOT NULL,"
                "status TEXT NOT NULL DEFAULT 'PENDING',"
                "screenshot_file_id TEXT,"
                "admin_id INTEGER,"
                "created_at INTEGER,"
                "decided_at INTEGER)"
            )
    await _conn.commit()


def get_db() -> aiosqlite.Connection:
    if _conn is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _conn


async def close_db() -> None:
    global _conn
    if _conn is not None:
        await _conn.close()
        _conn = None
