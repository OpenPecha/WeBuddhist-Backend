from typing import Any, Dict

from fastapi import HTTPException

from pecha_api.config import get
from pecha_api.shared.sqs_client import send_sqs_message

EVENT_CREATED_EVENT = "EVENT_CREATED"
EVENT_REMINDER_EVENT = "EVENT_REMINDER"
EVENT_NOTIFICATION_EVENT_VERSION = 1


def get_event_notification_sqs_queue_url() -> str:
    return get("EVENT_NOTIFICATION_SQS_QUEUE_URL").strip()


def is_event_notification_sqs_configured() -> bool:
    return bool(get_event_notification_sqs_queue_url())


def build_event_notification_event_body(*, event_id: str) -> Dict[str, Any]:
    return {
        "event_type": EVENT_CREATED_EVENT,
        "version": EVENT_NOTIFICATION_EVENT_VERSION,
        "event_id": event_id,
    }


def build_event_reminder_event_body(*, event_id: str, reminder_type: str) -> Dict[str, Any]:
    return {
        "event_type": EVENT_REMINDER_EVENT,
        "version": EVENT_NOTIFICATION_EVENT_VERSION,
        "event_id": event_id,
        "reminder_type": reminder_type,
    }


def send_event_notification_message(message_body: Dict[str, Any]) -> str:
    queue_url = get_event_notification_sqs_queue_url()
    try:
        return send_sqs_message(queue_url, message_body, service_name="Event")
    except HTTPException as e:
        raise RuntimeError(e.detail) from e
