from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient
from starlette import status

from pecha_api.app import api
from pecha_api.verse_of_day.verse_of_day_notification_response_models import (
    VerseOfDayNotificationTargetsResponse,
)

client = TestClient(api)

ENDPOINT = "/internal/verse-of-day-notification-targets"


def test_missing_dispatch_token_returns_422():
    response = client.get(ENDPOINT)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_wrong_dispatch_token_returns_401():
    with patch(
        "pecha_api.routines.routine_notifications.dependencies.get",
        return_value="expected-secret",
    ):
        response = client.get(ENDPOINT, headers={"X-Dispatch-Token": "wrong-secret"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_valid_dispatch_token_returns_targets():
    empty_response = VerseOfDayNotificationTargetsResponse(
        generated_at=datetime.now(timezone.utc),
        users=[],
    )
    with patch(
        "pecha_api.routines.routine_notifications.dependencies.get",
        return_value="expected-secret",
    ), patch(
        "pecha_api.verse_of_day.verse_of_day_notification_internal_views.get_verse_of_day_notification_targets",
        return_value=empty_response,
    ):
        response = client.get(ENDPOINT, headers={"X-Dispatch-Token": "expected-secret"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["users"] == []
