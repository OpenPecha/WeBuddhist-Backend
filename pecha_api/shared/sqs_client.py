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


def send_sqs_message(queue_url: str, message_body: Dict[str, Any], service_name: str = "SQS") -> str:
    """Send a message to an SQS queue.

    Args:
        queue_url: The SQS queue URL
        message_body: The message body as a dictionary
        service_name: The service name for error messages (e.g., 'Audio', 'Chat')

    Returns:
        The message ID returned by SQS

    Raises:
        HTTPException: If queue is not configured or message send fails
    """
    if not queue_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{service_name} SQS queue is not configured",
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
        logger.error("Failed to enqueue %s job to SQS: %s", service_name.lower(), e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to enqueue {service_name.lower()} job",
        ) from e
    except Exception as e:
        logger.error("Unexpected error enqueueing %s job: %s", service_name.lower(), e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to enqueue {service_name.lower()} job",
        ) from e
