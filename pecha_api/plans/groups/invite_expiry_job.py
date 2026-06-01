import asyncio
import logging

from pecha_api.db.database import SessionLocal
from pecha_api.plans.groups.groups_repository import expire_pending_invites

INVITE_EXPIRY_INTERVAL_SECONDS = 300


async def run_invite_expiry_scheduler() -> None:
    while True:
        await asyncio.sleep(INVITE_EXPIRY_INTERVAL_SECONDS)
        try:
            await asyncio.to_thread(_expire_once)
        except Exception as exc:
            logging.exception("Group invite expiry job failed: %s", exc)


def _expire_once() -> None:
    with SessionLocal() as db:
        count = expire_pending_invites(db=db)
    if count:
        logging.info("Expired %s pending group invite(s)", count)
