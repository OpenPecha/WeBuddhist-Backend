from unittest.mock import patch

import pytest
from fastapi import HTTPException
from starlette import status

from pecha_api.events.notification_sqs_client import (
    EVENT_CREATED_EVENT,
    EVENT_NOTIFICATION_EVENT_VERSION,
    EVENT_REMINDER_EVENT,
    build_event_notification_event_body,
    build_event_reminder_event_body,
    get_event_notification_sqs_queue_url,
    is_event_notification_sqs_configured,
    send_event_notification_message,
)


@patch("pecha_api.events.notification_sqs_client.get")
def test_get_event_notification_sqs_queue_url_strips_whitespace(mock_get):
    mock_get.return_value = "  https://sqs.example.com/queue  "

    assert get_event_notification_sqs_queue_url() == "https://sqs.example.com/queue"
    mock_get.assert_called_once_with("EVENT_NOTIFICATION_SQS_QUEUE_URL")


@patch("pecha_api.events.notification_sqs_client.get")
def test_is_event_notification_sqs_configured_true_when_url_present(mock_get):
    mock_get.return_value = "https://sqs.example.com/queue"

    assert is_event_notification_sqs_configured() is True


@patch("pecha_api.events.notification_sqs_client.get")
def test_is_event_notification_sqs_configured_false_when_url_missing(mock_get):
    mock_get.return_value = ""

    assert is_event_notification_sqs_configured() is False


def test_build_event_notification_event_body():
    body = build_event_notification_event_body(event_id="event-1")

    assert body == {
        "event_type": EVENT_CREATED_EVENT,
        "version": EVENT_NOTIFICATION_EVENT_VERSION,
        "event_id": "event-1",
    }


def test_build_event_reminder_event_body():
    body = build_event_reminder_event_body(
        event_id="event-1", reminder_type="ONE_DAY_BEFORE", fire_at="2026-01-01T00:00:00+00:00",
    )

    assert body == {
        "event_type": EVENT_REMINDER_EVENT,
        "version": EVENT_NOTIFICATION_EVENT_VERSION,
        "event_id": "event-1",
        "reminder_type": "ONE_DAY_BEFORE",
        "fire_at": "2026-01-01T00:00:00+00:00",
    }


@patch("pecha_api.events.notification_sqs_client.send_sqs_message")
@patch("pecha_api.events.notification_sqs_client.get")
def test_send_event_notification_message_success(mock_get, mock_send):
    mock_get.return_value = "https://sqs.example.com/queue"
    mock_send.return_value = "message-123"

    message_id = send_event_notification_message({"event_type": EVENT_CREATED_EVENT})

    assert message_id == "message-123"
    mock_send.assert_called_once_with(
        "https://sqs.example.com/queue", {"event_type": EVENT_CREATED_EVENT}, service_name="Event",
    )


@patch("pecha_api.events.notification_sqs_client.send_sqs_message")
@patch("pecha_api.events.notification_sqs_client.get")
def test_send_event_notification_message_wraps_http_exception_as_runtime_error(mock_get, mock_send):
    mock_get.return_value = "https://sqs.example.com/queue"
    mock_send.side_effect = HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="SQS not configured",
    )

    with pytest.raises(RuntimeError) as exc_info:
        send_event_notification_message({"event_type": EVENT_CREATED_EVENT})

    assert str(exc_info.value) == "SQS not configured"
