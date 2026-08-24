from typing import Any, Dict

from fastapi import HTTPException

from pecha_api.config import get
from pecha_api.shared.sqs_client import send_sqs_message

GROUP_POST_CREATED_EVENT = "GROUP_POST_CREATED"
GROUP_POST_NOTIFICATION_EVENT_VERSION = 1


def get_group_post_notification_sqs_queue_url() -> str:
    return get("GROUP_POST_NOTIFICATION_SQS_QUEUE_URL").strip()


def is_group_post_notification_sqs_configured() -> bool:
    return bool(get_group_post_notification_sqs_queue_url())


def build_group_post_notification_event_body(*, post_id: str) -> Dict[str, Any]:
    return {
        "event_type": GROUP_POST_CREATED_EVENT,
        "version": GROUP_POST_NOTIFICATION_EVENT_VERSION,
        "post_id": post_id,
    }


def send_group_post_notification_message(message_body: Dict[str, Any]) -> str:
    queue_url = get_group_post_notification_sqs_queue_url()
    try:
        return send_sqs_message(queue_url, message_body, service_name="GroupPost")
    except HTTPException as e:
        raise RuntimeError(e.detail) from e
