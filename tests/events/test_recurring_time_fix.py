"""Regression check: recurring events keep the time-of-day the client sent,
instead of always landing on midnight."""
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from pecha_api.app import api
from pecha_api.events.recurrence_service import combine_date_with_time_of_day

client = TestClient(api)
M = "pecha_api.events.event_service"
AUTH = {"Authorization": "Bearer token"}
GROUP = str(uuid4())


def test_combine_date_with_time_of_day_applies_utc_time_to_new_date():
    occurrence = date(2027, 3, 10)
    reference = datetime(2020, 1, 1, 9, 30, 0, tzinfo=timezone.utc)
    result = combine_date_with_time_of_day(occurrence, reference)
    assert result == datetime(2027, 3, 10, 9, 30, 0, tzinfo=timezone.utc)


def test_combine_date_with_time_of_day_normalizes_non_utc_reference():
    occurrence = date(2027, 3, 10)
    # +05:30 (IST) 15:00 == 09:30 UTC
    reference = datetime(2020, 1, 1, 15, 0, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    result = combine_date_with_time_of_day(occurrence, reference)
    assert result == datetime(2027, 3, 10, 9, 30, 0, tzinfo=timezone.utc)


def _row(ev, md):
    return SimpleNamespace(
        id=uuid4(), plan_id=None, accumulator_id=None, mantra_id=None, timer_id=None,
        group_recitation_collection_id=None, group_id=ev.group_id, location_id=None,
        location=None, start_date=ev.start_date, end_date=ev.end_date, image_url=None,
        featured=False, is_recurring=bool(ev.is_recurring),
        recurrence_frequency=ev.recurrence_frequency,
        recurrence_date_system=ev.recurrence_date_system,
        recurrence_calendar_type=ev.recurrence_calendar_type,
        recurrence_month=ev.recurrence_month, recurrence_day=ev.recurrence_day,
        duration_days=ev.duration_days,
        metadata_entries=[SimpleNamespace(id=uuid4(), name=m.name,
                                          description=m.description, language=m.language)
                          for m in md],
        links=[], created_at=datetime.now(timezone.utc),
        created_by=ev.created_by, updated_at=None,
    )


def _post(payload):
    with patch(f"{M}.validate_cms_author_details",
               return_value=SimpleNamespace(id=uuid4(), email="a@e.com")), \
         patch(f"{M}.require_can_create_content"), patch(f"{M}.SessionLocal"), \
         patch(f"{M}.enqueue_event_notification"), \
         patch(f"{M}.save_event", side_effect=lambda db, e, md, li=None: _row(e, md)):
        return client.post("/cms/events", json=payload, headers=AUTH)


def test_create_recurring_event_keeps_the_sent_time_of_day():
    payload = {
        "group_id": GROUP,
        "metadata": [{"name": "Monthly Tsok", "language": "EN"}],
        "start_date": "2026-09-13T09:30:00Z",
        "end_date": "2026-09-13T17:00:00Z",
        "recurrence": {"frequency": "MONTHLY", "date_system": "GREGORIAN",
                       "day": 10, "duration_days": 1},
    }
    response = _post(payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["start_date"].endswith("T09:30:00Z"), body["start_date"]
    assert body["end_date"].endswith("T17:00:00Z"), body["end_date"]


def test_create_recurring_event_without_times_still_defaults_to_midnight():
    payload = {
        "group_id": GROUP,
        "metadata": [{"name": "Monthly Tsok", "language": "EN"}],
        "recurrence": {"frequency": "MONTHLY", "date_system": "GREGORIAN",
                       "day": 10, "duration_days": 1},
    }
    response = _post(payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["start_date"].endswith("T00:00:00Z"), body["start_date"]
