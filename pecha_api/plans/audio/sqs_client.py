import json
import logging
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from starlette import status

from pecha_api.config import get

logger = logging.getLogger(__name__)

_sqs_client = None


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


def get_audio_sqs_queue_url() -> str:
    return get("AUDIO_SQS_QUEUE_URL").strip()


def is_audio_sqs_configured() -> bool:
    return bool(get_audio_sqs_queue_url())


def send_audio_job_message(message_body: Dict[str, Any]) -> str:
    queue_url = get_audio_sqs_queue_url()
    if not queue_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Audio SQS queue is not configured",
        )

    try:
        response = _get_sqs_client().send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body, default=str),
        )
        message_id = response.get("MessageId")
        if not message_id:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="SQS did not return a MessageId",
            )
        return message_id
    except HTTPException:
        raise
    except ClientError as e:
        logger.error("Failed to enqueue audio job to SQS: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to enqueue audio generation job",
        ) from e
    except Exception as e:
        logger.error("Unexpected error enqueueing audio job: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to enqueue audio generation job",
        ) from e
