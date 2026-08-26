from typing import Any, Dict

from fastapi import HTTPException

from pecha_api.config import get
from pecha_api.shared.sqs_client import send_sqs_message

CHAT_MESSAGE_CREATED_EVENT = "CHAT_MESSAGE_CREATED"
CHAT_NOTIFICATION_EVENT_VERSION = 1


def get_chat_notification_sqs_queue_url() -> str:
    return get("CHAT_NOTIFICATION_SQS_QUEUE_URL").strip()


def is_chat_notification_sqs_configured() -> bool:
    return bool(get_chat_notification_sqs_queue_url())


def build_chat_notification_event_body(*, message_id: str) -> Dict[str, Any]:
    return {
        "event_type": CHAT_MESSAGE_CREATED_EVENT,
        "version": CHAT_NOTIFICATION_EVENT_VERSION,
        "message_id": message_id,
    }


def send_chat_notification_message(message_body: Dict[str, Any]) -> str:
    queue_url = get_chat_notification_sqs_queue_url()
    try:
        return send_sqs_message(queue_url, message_body, service_name="Chat")
    except HTTPException as e:
        raise RuntimeError(e.detail) from e
