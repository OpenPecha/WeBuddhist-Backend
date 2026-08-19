from typing import Any, Dict

from pecha_api.config import get
from pecha_api.shared.sqs_client import send_sqs_message


def get_audio_sqs_queue_url() -> str:
    return get("AUDIO_SQS_QUEUE_URL").strip()


def is_audio_sqs_configured() -> bool:
    return bool(get_audio_sqs_queue_url())


def send_audio_job_message(message_body: Dict[str, Any]) -> str:
    queue_url = get_audio_sqs_queue_url()
    return send_sqs_message(queue_url, message_body, service_name="Audio")
