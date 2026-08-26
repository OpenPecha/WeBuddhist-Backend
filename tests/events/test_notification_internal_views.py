from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from pecha_api.app import api
from pecha_api.events.notification_response_models import EventReminderTargetsResponse

client = TestClient(api)


def test_event_reminder_targets_requires_dispatch_token():
    response = client.get(f"/internal/event-reminder-targets/{uuid4()}?reminder_type=T_ZERO")
    assert response.status_code == 422


def test_event_reminder_targets_returns_targets_with_computed_minutes_before():
    event_id = uuid4()
    empty_response = EventReminderTargetsResponse(
        event_id=event_id,
        reminder_type="T_MINUS_10",
        title="Full Moon Meditation",
        body="Starting in 10 minutes",
        recipients=[],
        skip=0,
        limit=100,
        total=0,
        has_more=False,
    )

    with patch(
        "pecha_api.routines.routine_notifications.dependencies.get",
        return_value="expected-secret",
    ), patch(
        "pecha_api.events.notification_internal_views.get_int", return_value=10,
    ), patch(
        "pecha_api.events.notification_internal_views.get_event_reminder_targets",
        return_value=empty_response,
    ) as mock_targets:
        response = client.get(
            f"/internal/event-reminder-targets/{event_id}?reminder_type=T_MINUS_10",
            headers={"X-Dispatch-Token": "expected-secret"},
        )

    assert response.status_code == 200
    assert response.json()["title"] == "Full Moon Meditation"
    mock_targets.assert_called_once_with(
        event_id=event_id,
        reminder_type="T_MINUS_10",
        minutes_before=10,
        skip=0,
        limit=100,
    )
