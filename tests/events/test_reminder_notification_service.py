from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from pecha_api.events.event_reminder_service import REMINDER_TYPE_T_MINUS_10, REMINDER_TYPE_T_ZERO
from pecha_api.events.reminder_notification_service import (
    _build_reminder_copy,
    _get_event_name,
    _reminder_superseded,
    get_event_reminder_targets,
)

MODULE = "pecha_api.events.reminder_notification_service"


class MockMetadataEntry:
    def __init__(self, name, language="EN"):
        self.name = name
        self.language = language


class MockEvent:
    def __init__(self, event_id=None):
        self.id = event_id or uuid4()


class MockUser:
    def __init__(self, user_id=None):
        self.id = user_id or uuid4()


class MockDevice:
    def __init__(self, user_id, token="tok", platform="ANDROID"):
        self.id = uuid4()
        self.user_id = user_id
        self.token = token
        self.platform = platform


def _reminder(fire_at=None, canceled_at=None):
    return SimpleNamespace(
        fire_at=fire_at or datetime.now(timezone.utc) - timedelta(seconds=5),
        canceled_at=canceled_at,
    )


class TestReminderSuperseded:
    @patch(f"{MODULE}.get_event_reminder")
    def test_false_for_a_due_uncanceled_reminder(self, mock_get):
        mock_get.return_value = _reminder()
        assert _reminder_superseded(MagicMock(), uuid4(), REMINDER_TYPE_T_ZERO) is False

    @patch(f"{MODULE}.get_event_reminder")
    def test_true_when_canceled(self, mock_get):
        mock_get.return_value = _reminder(canceled_at=datetime.now(timezone.utc))
        assert _reminder_superseded(MagicMock(), uuid4(), REMINDER_TYPE_T_ZERO) is True

    @patch(f"{MODULE}.get_event_reminder")
    def test_true_when_fire_at_moved_into_the_future(self, mock_get):
        """Only a reschedule's upsert can push fire_at past now on a row
        that was legitimately due at dispatch time."""
        mock_get.return_value = _reminder(fire_at=datetime.now(timezone.utc) + timedelta(days=3))
        assert _reminder_superseded(MagicMock(), uuid4(), REMINDER_TYPE_T_ZERO) is True

    @patch(f"{MODULE}.get_event_reminder", return_value=None)
    def test_true_when_row_no_longer_exists(self, _mock_get):
        assert _reminder_superseded(MagicMock(), uuid4(), REMINDER_TYPE_T_ZERO) is True


class TestGetEventName:
    def test_prefers_english_entry(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [
            MockMetadataEntry("Tibetan name", language="BO"),
            MockMetadataEntry("English name", language="EN"),
        ]
        assert _get_event_name(db, uuid4()) == "English name"

    def test_falls_back_to_first_entry(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [
            MockMetadataEntry("Only name", language="BO"),
        ]
        assert _get_event_name(db, uuid4()) == "Only name"

    def test_falls_back_when_no_entries(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        assert _get_event_name(db, uuid4()) == "Your event"


class TestBuildReminderCopy:
    def test_t_minus_10_includes_minutes(self):
        assert _build_reminder_copy(
            reminder_type=REMINDER_TYPE_T_MINUS_10, event_name="Full Moon", minutes_before=10,
        ) == "Starting in 10 minutes"

    def test_t_zero_says_starting_now(self):
        assert _build_reminder_copy(
            reminder_type=REMINDER_TYPE_T_ZERO, event_name="Full Moon", minutes_before=10,
        ) == "Starting now"

    def test_unknown_type_falls_back_to_starting_now(self):
        assert _build_reminder_copy(
            reminder_type="SOMETHING_ELSE", event_name="Full Moon", minutes_before=10,
        ) == "Starting now"


class TestGetEventReminderTargets:
    @patch(f"{MODULE}.get_event_by_id", return_value=None)
    @patch(f"{MODULE}.SessionLocal")
    def test_missing_event_raises_404(self, mock_session, _get_event):
        mock_session.return_value.__enter__.return_value = MagicMock()
        with pytest.raises(HTTPException) as exc:
            get_event_reminder_targets(event_id=uuid4(), reminder_type=REMINDER_TYPE_T_ZERO, minutes_before=10)
        assert exc.value.status_code == 404

    @patch(f"{MODULE}._reminder_superseded", return_value=False)
    @patch(f"{MODULE}.normalize_platform", side_effect=lambda p: p)
    @patch(f"{MODULE}.get_active_push_devices_by_user_ids")
    @patch(f"{MODULE}.get_event_participants_paginated")
    @patch(f"{MODULE}._get_event_name", return_value="Full Moon Meditation")
    @patch(f"{MODULE}.get_event_by_id")
    @patch(f"{MODULE}.SessionLocal")
    def test_skips_recipients_without_devices_and_builds_body(
        self, mock_session, mock_get_event, _mock_name, mock_participants, mock_devices, _mock_platform, _superseded,
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        event = MockEvent()
        mock_get_event.return_value = event

        with_device = MockUser()
        without_device = MockUser()
        mock_participants.return_value = ([(with_device, None), (without_device, None)], 2)
        device = MockDevice(user_id=with_device.id)
        mock_devices.return_value = {with_device.id: [device]}

        result = get_event_reminder_targets(
            event_id=event.id, reminder_type=REMINDER_TYPE_T_MINUS_10, minutes_before=10,
        )

        assert result.event_id == event.id
        assert result.title == "Full Moon Meditation"
        assert result.body == "Starting in 10 minutes"
        assert len(result.recipients) == 1
        assert result.recipients[0].user_id == with_device.id
        assert result.total == 2
        assert result.has_more is False

    @patch(f"{MODULE}._reminder_superseded", return_value=False)
    @patch(f"{MODULE}.get_active_push_devices_by_user_ids", return_value={})
    @patch(f"{MODULE}.get_event_participants_paginated", return_value=([], 0))
    @patch(f"{MODULE}._get_event_name", return_value="Event")
    @patch(f"{MODULE}.get_event_by_id")
    @patch(f"{MODULE}.SessionLocal")
    def test_clamps_out_of_range_pagination(
        self, mock_session, mock_get_event, _mock_name, mock_participants, _mock_devices, _superseded,
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        event = MockEvent()
        mock_get_event.return_value = event

        result = get_event_reminder_targets(
            event_id=event.id,
            reminder_type=REMINDER_TYPE_T_ZERO,
            minutes_before=10,
            skip=-5,
            limit=10000,
        )

        assert result.skip == 0
        assert result.limit == 500
        assert mock_participants.call_args.kwargs["skip"] == 0
        assert mock_participants.call_args.kwargs["limit"] == 500

    @patch(f"{MODULE}._reminder_superseded", return_value=False)
    @patch(f"{MODULE}.get_active_push_devices_by_user_ids", return_value={})
    @patch(f"{MODULE}.get_event_participants_paginated", return_value=([], 0))
    @patch(f"{MODULE}._get_event_name", return_value="Event")
    @patch(f"{MODULE}.get_event_by_id")
    @patch(f"{MODULE}.SessionLocal")
    def test_limit_below_one_floors_to_one(
        self, mock_session, mock_get_event, _mock_name, mock_participants, _mock_devices, _superseded,
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        event = MockEvent()
        mock_get_event.return_value = event

        result = get_event_reminder_targets(
            event_id=event.id,
            reminder_type=REMINDER_TYPE_T_ZERO,
            minutes_before=10,
            limit=0,
        )

        assert result.limit == 1

    @patch(f"{MODULE}._reminder_superseded", return_value=True)
    @patch(f"{MODULE}.get_event_participants_paginated")
    @patch(f"{MODULE}.get_event_by_id")
    @patch(f"{MODULE}.SessionLocal")
    def test_superseded_reminder_returns_no_recipients(
        self, mock_session, mock_get_event, mock_participants, _superseded,
    ):
        """Regression guard: this is the final gate closest to actual push
        delivery - a canceled or rescheduled reminder must not reach anyone,
        even if a stale SQS message already made it this far."""
        mock_session.return_value.__enter__.return_value = MagicMock()
        event = MockEvent()
        mock_get_event.return_value = event

        result = get_event_reminder_targets(
            event_id=event.id, reminder_type=REMINDER_TYPE_T_MINUS_10, minutes_before=10,
        )

        assert result.recipients == []
        assert result.total == 0
        mock_participants.assert_not_called()
