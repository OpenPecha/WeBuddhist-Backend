from typing import Any, Dict

from fastapi import HTTPException

from pecha_api.config import get
from pecha_api.shared.sqs_client import send_sqs_message

JOIN_REQUEST_CREATED_EVENT = "JOIN_REQUEST_CREATED"
JOIN_REQUEST_DECIDED_EVENT = "JOIN_REQUEST_DECIDED"
JOIN_REQUEST_NOTIFICATION_EVENT_VERSION = 1


def get_join_request_notification_sqs_queue_url() -> str:
    return get("JOIN_REQUEST_NOTIFICATION_SQS_QUEUE_URL").strip()


def is_join_request_notification_sqs_configured() -> bool:
    return bool(get_join_request_notification_sqs_queue_url())


def build_join_request_event_body(*, join_request_id: str, event_type: str) -> Dict[str, Any]:
    return {
        "event_type": event_type,
        "version": JOIN_REQUEST_NOTIFICATION_EVENT_VERSION,
        "join_request_id": join_request_id,
    }


def send_join_request_notification_message(message_body: Dict[str, Any]) -> str:
    queue_url = get_join_request_notification_sqs_queue_url()
    try:
        return send_sqs_message(queue_url, message_body, service_name="JoinRequest")
    except HTTPException as e:
        raise RuntimeError(e.detail) from e
