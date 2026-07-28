import json
import logging
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

from pecha_api.config import get

logger = logging.getLogger(__name__)

_sqs_client = None

CHAT_MESSAGE_CREATED_EVENT = "CHAT_MESSAGE_CREATED"
CHAT_NOTIFICATION_EVENT_VERSION = 1


def _get_sqs_client():
    global _sqs_client
    if _sqs_client is None:
        _sqs_client = boto3.client(
            "sqs",
            aws_access_key_id=get("AWS_ACCESS_KEY"),
            aws_secret_access_key=get("AWS_SECRET_KEY"),
            region_name=get("AWS_REGION"),
        )
    return _sqs_client


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
    if not queue_url:
        raise RuntimeError("Chat notification SQS queue is not configured")

    try:
        response = _get_sqs_client().send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body, default=str),
        )
        message_id = response.get("MessageId")
        if not message_id:
            raise RuntimeError("SQS did not return a MessageId")
        return message_id
    except ClientError as e:
        logger.error("Failed to enqueue chat notification to SQS: %s", e)
        raise RuntimeError("Failed to enqueue chat notification") from e
