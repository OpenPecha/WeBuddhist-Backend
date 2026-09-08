from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

from pecha_api.events.event_reminder_service import (
    REMINDER_TYPE_T_MINUS_10,
    REMINDER_TYPE_T_ZERO,
    cancel_event_reminders,
    reschedule_event_reminders,
    schedule_event_reminders,
)

MODULE = "pecha_api.events.event_reminder_service"


class TestScheduleEventReminders:
    @patch(f"{MODULE}.get_int", return_value=10)
    @patch(f"{MODULE}.create_or_replace_reminder")
    def test_creates_both_reminders_for_a_future_event(self, mock_create, _get_int):
        db = MagicMock()
        event_id = uuid4()
        start_date = datetime.now(timezone.utc) + timedelta(days=1)

        schedule_event_reminders(db, event_id, start_date)

        assert mock_create.call_count == 2
        mock_create.assert_any_call(db, event_id, REMINDER_TYPE_T_MINUS_10, start_date - timedelta(minutes=10))
        mock_create.assert_any_call(db, event_id, REMINDER_TYPE_T_ZERO, start_date)
        db.commit.assert_not_called()

    @patch(f"{MODULE}.get_int", return_value=10)
    @patch(f"{MODULE}.create_or_replace_reminder")
    def test_skips_reminders_whose_fire_time_already_passed(self, mock_create, _get_int):
        db = MagicMock()
        event_id = uuid4()
        start_date = datetime.now(timezone.utc) - timedelta(minutes=1)

        schedule_event_reminders(db, event_id, start_date)

        mock_create.assert_not_called()

    @patch(f"{MODULE}.get_int", return_value=10)
    @patch(f"{MODULE}.create_or_replace_reminder")
    def test_creates_only_t_zero_when_t_minus_already_passed(self, mock_create, _get_int):
        db = MagicMock()
        event_id = uuid4()
        # 5 minutes out: T-minus-10 fire time is already in the past, T-zero is not.
        start_date = datetime.now(timezone.utc) + timedelta(minutes=5)

        schedule_event_reminders(db, event_id, start_date)

        mock_create.assert_called_once_with(db, event_id, REMINDER_TYPE_T_ZERO, start_date)

    @patch(f"{MODULE}.get_int", return_value=0)
    @patch(f"{MODULE}.create_or_replace_reminder")
    def test_minutes_before_floors_at_one(self, mock_create, _get_int):
        db = MagicMock()
        event_id = uuid4()
        start_date = datetime.now(timezone.utc) + timedelta(days=1)

        schedule_event_reminders(db, event_id, start_date)

        mock_create.assert_any_call(db, event_id, REMINDER_TYPE_T_MINUS_10, start_date - timedelta(minutes=1))


class TestRescheduleEventReminders:
    @patch(f"{MODULE}.get_int", return_value=10)
    @patch(f"{MODULE}.create_or_replace_reminder")
    @patch(f"{MODULE}.cancel_reminders_for_event")
    def test_cancels_then_recreates_in_the_same_session(self, mock_cancel, mock_create, _get_int):
        db = MagicMock()
        event_id = uuid4()
        new_start = datetime.now(timezone.utc) + timedelta(days=2)

        call_order = []
        mock_cancel.side_effect = lambda *a, **k: call_order.append("cancel")
        mock_create.side_effect = lambda *a, **k: call_order.append("create")

        reschedule_event_reminders(db, event_id, new_start)

        mock_cancel.assert_called_once_with(db, event_id)
        assert call_order[0] == "cancel"
        assert "create" in call_order
        db.commit.assert_not_called()


class TestCancelEventReminders:
    @patch(f"{MODULE}.cancel_reminders_for_event")
    def test_delegates_to_repository_without_committing(self, mock_cancel):
        db = MagicMock()
        event_id = uuid4()

        cancel_event_reminders(db, event_id)

        mock_cancel.assert_called_once_with(db, event_id)
        db.commit.assert_not_called()
