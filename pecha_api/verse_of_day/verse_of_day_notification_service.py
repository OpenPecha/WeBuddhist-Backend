from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, datetime, timezone, tzinfo
from typing import Optional
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from pecha_api.config import get
from pecha_api.db.database import SessionLocal
from pecha_api.verse_of_day import verse_of_day_notification_repository as repo
from pecha_api.verse_of_day.verse_of_day_notification_repository import VerseOfDayDeviceTargetRow
from pecha_api.verse_of_day.verse_of_day_notification_response_models import (
    VerseOfDayNotificationContentDTO,
    VerseOfDayNotificationTargetsResponse,
    VerseOfDayNotificationUserTargetDTO,
    VerseOfDayPushDeviceTargetDTO,
)
from pecha_api.verse_of_day.verse_of_day_model import VerseOfDay
from pecha_api.verse_of_day.verse_of_day_repository import get_verse_of_day_today
from pecha_api.verse_of_day.verse_of_day_service import build_verses_dict, _generate_verse_image_url

logger = logging.getLogger(__name__)

TARGET_LOCAL_HOUR = 10
TARGET_LOCAL_MINUTE = 0
DEFAULT_LANG = "en"


def get_verse_of_day_notification_targets() -> VerseOfDayNotificationTargetsResponse:
    utc_now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        rows = repo.get_active_device_targets(db)
        matched_rows = [row for row in rows if _local_time_matches(row.timezone, utc_now)]

        if not matched_rows:
            return VerseOfDayNotificationTargetsResponse(generated_at=utc_now, users=[])

        users = _build_user_targets(db, matched_rows, utc_now)

    return VerseOfDayNotificationTargetsResponse(generated_at=utc_now, users=users)


def _resolve_zoneinfo(timezone_name: Optional[str]) -> tzinfo:
    name = (timezone_name or "").strip()
    if not name or name.upper() == "UTC":
        return timezone.utc
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        logger.warning("Unknown timezone %r on user metadata; falling back to UTC", name)
        return timezone.utc


def _local_time_matches(timezone_name: Optional[str], utc_now: datetime) -> bool:
    tz = _resolve_zoneinfo(timezone_name)
    local_now = utc_now.astimezone(tz)
    return local_now.hour == TARGET_LOCAL_HOUR and local_now.minute == TARGET_LOCAL_MINUTE


def _build_user_targets(
    db: Session,
    matched_rows: list[VerseOfDayDeviceTargetRow],
    utc_now: datetime,
) -> list[VerseOfDayNotificationUserTargetDTO]:
    rows_by_local_date: dict[date, list[VerseOfDayDeviceTargetRow]] = defaultdict(list)
    for row in matched_rows:
        tz = _resolve_zoneinfo(row.timezone)
        local_date = utc_now.astimezone(tz).date()
        rows_by_local_date[local_date].append(row)

    verse_by_date: dict[date, Optional[VerseOfDay]] = {
        local_date: get_verse_of_day_today(db, local_date) for local_date in rows_by_local_date
    }

    users_by_id: dict[UUID, list[tuple[VerseOfDayDeviceTargetRow, Optional[VerseOfDay]]]] = defaultdict(list)
    for local_date, date_rows in rows_by_local_date.items():
        verse = verse_by_date[local_date]
        for row in date_rows:
            users_by_id[row.user_id].append((row, verse))

    targets: list[VerseOfDayNotificationUserTargetDTO] = []
    for user_id, entries in sorted(users_by_id.items(), key=lambda item: str(item[0])):
        row0, verse = entries[0]
        content = _resolve_notification_content(verse, row0.language)
        if content is None:
            continue

        devices: list[VerseOfDayPushDeviceTargetDTO] = []
        seen_tokens: set[str] = set()
        for row, _verse in entries:
            if row.device_token in seen_tokens:
                continue
            seen_tokens.add(row.device_token)
            devices.append(VerseOfDayPushDeviceTargetDTO(token=row.device_token, platform=row.platform))

        targets.append(
            VerseOfDayNotificationUserTargetDTO(
                user_id=user_id,
                notification=content,
                push_devices=devices,
            )
        )

    return targets


def _resolve_notification_content(
    verse: Optional[VerseOfDay],
    user_language: Optional[str],
) -> Optional[VerseOfDayNotificationContentDTO]:
    if verse is None or not verse.verse_metadata:
        logger.warning("No verse-of-day published for date=%s; skipping notification", verse.date if verse else None)
        return None

    verses_dict = build_verses_dict(verse.verse_metadata)
    verses_by_lang = {lang.lower(): text for lang, text in verses_dict.items()}
    effective_lang = (user_language or "EN").lower()

    body = verses_by_lang.get(effective_lang) or verses_by_lang.get(DEFAULT_LANG)
    if body is None:
        logger.warning(
            "No verse-of-day text for lang=%s or fallback '%s' on date=%s; skipping notification",
            effective_lang,
            DEFAULT_LANG,
            verse.date,
        )
        return None

    return VerseOfDayNotificationContentDTO(
        title=get("VERSE_OF_DAY_NOTIFICATION_TITLE"),
        body=body,
        image_url=_generate_verse_image_url(verse.image_urls),
    )
