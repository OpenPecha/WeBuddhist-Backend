import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from pecha_api.config import get_int
from pecha_api.verse_of_day.verse_of_day_service import cleanup_expired_verses_of_day

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def setup_scheduler() -> None:
    expiry_days = get_int("VERSE_OF_DAY_EXPIRY_DAYS")
    if expiry_days < 1:
        raise ValueError(
            f"VERSE_OF_DAY_EXPIRY_DAYS must be a positive integer, got {expiry_days}"
        )
    scheduler.add_job(
        cleanup_expired_verses_of_day,
        CronTrigger(hour=0, minute=0),
        args=[expiry_days],
        id="cleanup_expired_verses_of_day",
        name="Cleanup expired verses of the day",
        replace_existing=True,
    )
    if not scheduler.running:
        scheduler.start()
    logger.info(
        "Scheduler started: cleaning verses of the day older than %s day(s) daily at midnight",
        expiry_days,
    )


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down")
