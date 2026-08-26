"""Covers the reminder side effects wired into create/update event flows:
which branch schedules, reschedules, or cancels reminders, and that the
reminder mutation shares the same session as the event write."""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from pecha_api.events.event_response_models import (
    CreateEventRequest,
    RecurrenceInput,
    UpdateEventRequest,
)
from pecha_api.events.event_service import create_event_service, update_event_service

MODULE = "pecha_api.events.event_service"


def _author() -> SimpleNamespace:
    return SimpleNamespace(id=uuid4(), email="author@example.com")


def _event_stub(group_id=None, is_recurring=False, start_date=None) -> SimpleNamespace:
    now = start_date or datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        plan_id=None,
        accumulator_id=None,
        mantra_id=None,
        timer_id=None,
        group_recitation_collection_id=None,
        group_id=group_id or uuid4(),
        location_id=None,
        location=None,
        start_date=now,
        end_date=now,
        image_url=None,
        featured=False,
        is_recurring=is_recurring,
        recurrence_frequency="YEARLY" if is_recurring else None,
        recurrence_date_system="GREGORIAN" if is_recurring else None,
        recurrence_calendar_type=None,
        recurrence_month=6 if is_recurring else None,
        recurrence_day=15 if is_recurring else None,
        duration_days=1,
        metadata_entries=[],
        links=[],
        created_at=now,
        created_by="author@example.com",
        updated_at=None,
    )


def _create_request(group_id, recurrence=None) -> CreateEventRequest:
    now = datetime.now(timezone.utc)
    payload = {
        "group_id": group_id,
        "metadata": [{"name": "Event", "language": "EN"}],
    }
    if recurrence is not None:
        payload["recurrence"] = recurrence
    else:
        payload["start_date"] = now
        payload["end_date"] = now
    return CreateEventRequest(**payload)


def _recurrence() -> RecurrenceInput:
    return RecurrenceInput(frequency="YEARLY", date_system="GREGORIAN", month=6, day=15)


class TestCreateEventSchedulesReminders:
    def test_non_recurring_event_schedules_reminders_and_commits(self) -> None:
        group_id = uuid4()
        saved = _event_stub(group_id=group_id, is_recurring=False)
        request = _create_request(group_id)
        mock_db = MagicMock()

        with patch(f"{MODULE}.validate_cms_author_details", return_value=_author()), patch(
            f"{MODULE}.require_can_create_content"
        ), patch(f"{MODULE}.SessionLocal") as mock_session, patch(
            f"{MODULE}.save_event", return_value=saved
        ), patch(
            f"{MODULE}.enqueue_event_notification"
        ), patch(
            f"{MODULE}.schedule_event_reminders"
        ) as mock_schedule:
            mock_session.return_value.__enter__.return_value = mock_db

            create_event_service(token="token", request=request)

        mock_schedule.assert_called_once_with(mock_db, saved.id, saved.start_date)
        mock_db.commit.assert_called_once()

    def test_recurring_event_skips_reminder_scheduling(self) -> None:
        group_id = uuid4()
        saved = _event_stub(group_id=group_id, is_recurring=True)
        request = _create_request(group_id, recurrence=_recurrence())
        mock_db = MagicMock()

        with patch(f"{MODULE}.validate_cms_author_details", return_value=_author()), patch(
            f"{MODULE}.require_can_create_content"
        ), patch(f"{MODULE}.SessionLocal") as mock_session, patch(
            f"{MODULE}.save_event", return_value=saved
        ), patch(
            f"{MODULE}.enqueue_event_notification"
        ), patch(
            f"{MODULE}.schedule_event_reminders"
        ) as mock_schedule:
            mock_session.return_value.__enter__.return_value = mock_db

            create_event_service(token="token", request=request)

        mock_schedule.assert_not_called()
        mock_db.commit.assert_not_called()


class TestUpdateEventReminderBranches:
    def test_converting_to_recurring_cancels_reminders(self) -> None:
        group_id = uuid4()
        existing = _event_stub(group_id=group_id, is_recurring=False)
        request = UpdateEventRequest(recurrence=_recurrence())
        mock_db = MagicMock()

        with patch(f"{MODULE}.validate_cms_author_details", return_value=_author()), patch(
            f"{MODULE}._require_can_edit_event"
        ), patch(f"{MODULE}.SessionLocal") as mock_session, patch(
            f"{MODULE}.get_event_by_id", return_value=existing
        ), patch(
            f"{MODULE}.update_event", side_effect=lambda db, event, **kwargs: event
        ), patch(
            f"{MODULE}.cancel_event_reminders"
        ) as mock_cancel, patch(
            f"{MODULE}.reschedule_event_reminders"
        ) as mock_reschedule:
            mock_session.return_value.__enter__.return_value = mock_db

            update_event_service(token="token", event_id=existing.id, request=request)

        mock_cancel.assert_called_once_with(mock_db, existing.id)
        mock_reschedule.assert_not_called()
        assert existing.is_recurring is True

    def test_changing_start_date_on_non_recurring_event_reschedules(self) -> None:
        group_id = uuid4()
        existing = _event_stub(group_id=group_id, is_recurring=False)
        new_start = existing.start_date.replace(year=existing.start_date.year + 1)
        request = UpdateEventRequest(start_date=new_start, end_date=new_start)
        mock_db = MagicMock()

        with patch(f"{MODULE}.validate_cms_author_details", return_value=_author()), patch(
            f"{MODULE}._require_can_edit_event"
        ), patch(f"{MODULE}.SessionLocal") as mock_session, patch(
            f"{MODULE}.get_event_by_id", return_value=existing
        ), patch(
            f"{MODULE}.update_event", side_effect=lambda db, event, **kwargs: event
        ), patch(
            f"{MODULE}.cancel_event_reminders"
        ) as mock_cancel, patch(
            f"{MODULE}.reschedule_event_reminders"
        ) as mock_reschedule:
            mock_session.return_value.__enter__.return_value = mock_db

            update_event_service(token="token", event_id=existing.id, request=request)

        mock_reschedule.assert_called_once_with(mock_db, existing.id, new_start)
        mock_cancel.assert_not_called()

    def test_unrelated_field_change_does_not_touch_reminders(self) -> None:
        group_id = uuid4()
        existing = _event_stub(group_id=group_id, is_recurring=False)
        request = UpdateEventRequest(image_url="https://example.com/banner.png")
        mock_db = MagicMock()

        with patch(f"{MODULE}.validate_cms_author_details", return_value=_author()), patch(
            f"{MODULE}._require_can_edit_event"
        ), patch(f"{MODULE}.SessionLocal") as mock_session, patch(
            f"{MODULE}.get_event_by_id", return_value=existing
        ), patch(
            f"{MODULE}.update_event", side_effect=lambda db, event, **kwargs: event
        ), patch(
            f"{MODULE}.cancel_event_reminders"
        ) as mock_cancel, patch(
            f"{MODULE}.reschedule_event_reminders"
        ) as mock_reschedule:
            mock_session.return_value.__enter__.return_value = mock_db

            update_event_service(token="token", event_id=existing.id, request=request)

        mock_cancel.assert_not_called()
        mock_reschedule.assert_not_called()

    def test_already_recurring_event_start_date_change_does_not_reschedule(self) -> None:
        """start_date on a recurring event is driven by recurrence rules, not
        a direct edit, so a stray start_date change must not schedule reminders
        (which are out of scope for recurring events)."""
        group_id = uuid4()
        existing = _event_stub(group_id=group_id, is_recurring=True)
        request = UpdateEventRequest(
            start_date=existing.start_date.replace(year=existing.start_date.year + 1),
            end_date=existing.end_date.replace(year=existing.end_date.year + 1),
        )
        mock_db = MagicMock()

        with patch(f"{MODULE}.validate_cms_author_details", return_value=_author()), patch(
            f"{MODULE}._require_can_edit_event"
        ), patch(f"{MODULE}.SessionLocal") as mock_session, patch(
            f"{MODULE}.get_event_by_id", return_value=existing
        ), patch(
            f"{MODULE}.update_event", side_effect=lambda db, event, **kwargs: event
        ), patch(
            f"{MODULE}.cancel_event_reminders"
        ) as mock_cancel, patch(
            f"{MODULE}.reschedule_event_reminders"
        ) as mock_reschedule:
            mock_session.return_value.__enter__.return_value = mock_db

            update_event_service(token="token", event_id=existing.id, request=request)

        mock_cancel.assert_not_called()
        mock_reschedule.assert_not_called()

    def test_timezone_change_is_applied_to_the_event(self) -> None:
        group_id = uuid4()
        existing = _event_stub(group_id=group_id, is_recurring=False)
        request = UpdateEventRequest(timezone="America/New_York")
        mock_db = MagicMock()

        with patch(f"{MODULE}.validate_cms_author_details", return_value=_author()), patch(
            f"{MODULE}._require_can_edit_event"
        ), patch(f"{MODULE}.SessionLocal") as mock_session, patch(
            f"{MODULE}.get_event_by_id", return_value=existing
        ), patch(
            f"{MODULE}.update_event", side_effect=lambda db, event, **kwargs: event
        ):
            mock_session.return_value.__enter__.return_value = mock_db

            update_event_service(token="token", event_id=existing.id, request=request)

        assert existing.timezone == "America/New_York"

    def test_reminder_mutation_happens_before_event_persistence(self) -> None:
        """The reminder call must be queued in the same session before
        update_event's commit, not after, so a later persistence failure
        rolls both back together instead of leaving reminders stale."""
        group_id = uuid4()
        existing = _event_stub(group_id=group_id, is_recurring=False)
        new_start = existing.start_date.replace(year=existing.start_date.year + 1)
        request = UpdateEventRequest(start_date=new_start, end_date=new_start)
        mock_db = MagicMock()

        call_order = []

        def _record_reschedule(db, event_id, start_date):
            call_order.append("reschedule")

        def _record_update_event(db, event, **kwargs):
            call_order.append("update_event")
            return event

        with patch(f"{MODULE}.validate_cms_author_details", return_value=_author()), patch(
            f"{MODULE}._require_can_edit_event"
        ), patch(f"{MODULE}.SessionLocal") as mock_session, patch(
            f"{MODULE}.get_event_by_id", return_value=existing
        ), patch(
            f"{MODULE}.update_event", side_effect=_record_update_event
        ), patch(
            f"{MODULE}.reschedule_event_reminders", side_effect=_record_reschedule
        ):
            mock_session.return_value.__enter__.return_value = mock_db

            update_event_service(token="token", event_id=existing.id, request=request)

        assert call_order == ["reschedule", "update_event"]
