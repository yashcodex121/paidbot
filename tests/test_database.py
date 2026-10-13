"""Run: python -m tests.test_database  (DB layer ke duplicate-approval guards check karta hai)"""
import asyncio
import os
import tempfile

from app import database
from app.database import payments, users


async def main():
    path = os.path.join(tempfile.mkdtemp(), "t.db")
    await database.init_db(path)
    await payments.create("PAY-1", 1, "u", 99, "fid")
    assert await payments.user_has_pending(1)
    assert await payments.decide("PAY-1", payments.APPROVED, 9) is True
    assert await payments.decide("PAY-1", payments.APPROVED, 9) is False   # duplicate approve
    assert await payments.decide("PAY-1", payments.REJECTED, 9) is False   # approve ke baad reject
    assert await payments.claim_link_slot("PAY-1") is True
    assert await payments.claim_link_slot("PAY-1") is False                # duplicate link
    # users / broadcast helpers
    assert await users.upsert(1, "a", "A") is True      # naya user
    assert await users.upsert(1, "a", "A") is False     # existing
    await users.upsert(2, "b", "B")
    assert sorted(await users.active_ids()) == [1, 2]
    await users.mark_blocked(2)
    assert await users.active_ids() == [1]
    assert await users.counts() == (2, 1)
    await users.upsert(2, "b", "B")                     # /start dubara -> unblock
    assert sorted(await users.active_ids()) == [1, 2]
    st = await payments.stats()
    assert st["APPROVED"] == 1 and st["revenue"] == 99
    await database.close_db()
    print("ALL OK")


if __name__ == "__main__":
    asyncio.run(main())
