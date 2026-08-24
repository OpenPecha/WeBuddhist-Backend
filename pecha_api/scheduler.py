import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from pecha_api.chat.notification_dispatch_service import (
    reconcile_undispatched_chat_notifications,
)
from pecha_api.plans.groups.join_request_dispatch_service import (
    reconcile_undispatched_join_request_notifications,
)
from pecha_api.config import get_int
from pecha_api.plans.audio.audio_job_service import reconcile_undispatched_audio_jobs
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

    reconcile_interval = max(get_int("AUDIO_JOB_DISPATCH_RECONCILE_INTERVAL_SECONDS"), 1)
    scheduler.add_job(
        reconcile_undispatched_audio_jobs,
        IntervalTrigger(seconds=reconcile_interval),
        id="reconcile_undispatched_audio_jobs",
        name="Fail undispatched pending audio jobs",
        replace_existing=True,
    )

    chat_reconcile_interval = max(
        get_int("CHAT_NOTIFICATION_DISPATCH_RECONCILE_INTERVAL_SECONDS"),
        1,
    )
    scheduler.add_job(
        reconcile_undispatched_chat_notifications,
        IntervalTrigger(seconds=chat_reconcile_interval),
        id="reconcile_undispatched_chat_notifications",
        name="Re-enqueue undispatched chat notifications",
        replace_existing=True,
    )

    join_request_reconcile_interval = max(
        get_int("JOIN_REQUEST_NOTIFICATION_DISPATCH_RECONCILE_INTERVAL_SECONDS"),
        1,
    )
    scheduler.add_job(
        reconcile_undispatched_join_request_notifications,
        IntervalTrigger(seconds=join_request_reconcile_interval),
        id="reconcile_undispatched_join_request_notifications",
        name="Re-enqueue undispatched join request notifications",
        replace_existing=True,
    )

    if not scheduler.running:
        scheduler.start()
    logger.info(
        "Scheduler started: cleaning verses of the day older than %s day(s) daily at midnight; "
        "failing undispatched audio jobs every %s second(s); "
        "re-enqueueing undispatched chat notifications every %s second(s)",
        expiry_days,
        reconcile_interval,
        chat_reconcile_interval,
    )


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down")
