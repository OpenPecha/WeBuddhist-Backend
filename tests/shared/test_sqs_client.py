from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from fastapi import HTTPException
from starlette import status

from pecha_api.shared.sqs_client import send_sqs_message


@patch("pecha_api.shared.sqs_client._get_sqs_client")
def test_send_sqs_message_success(mock_get_client):
    mock_client = MagicMock()
    mock_client.send_message.return_value = {"MessageId": "test-123"}
    mock_get_client.return_value = mock_client

    message_id = send_sqs_message(
        queue_url="https://sqs.us-east-1.amazonaws.com/123456789/test-queue",
        message_body={"key": "value"},
        service_name="Audio"
    )

    assert message_id == "test-123"
    mock_client.send_message.assert_called_once()


@patch("pecha_api.shared.sqs_client._get_sqs_client")
def test_send_sqs_message_missing_queue_url(mock_get_client):
    with pytest.raises(HTTPException) as exc_info:
        send_sqs_message(
            queue_url="",
            message_body={"key": "value"},
            service_name="Audio"
        )

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "not configured" in exc_info.value.detail


@patch("pecha_api.shared.sqs_client._get_sqs_client")
def test_send_sqs_message_no_message_id_response(mock_get_client):
    mock_client = MagicMock()
    mock_client.send_message.return_value = {}
    mock_get_client.return_value = mock_client

    with pytest.raises(HTTPException) as exc_info:
        send_sqs_message(
            queue_url="https://sqs.us-east-1.amazonaws.com/123456789/test-queue",
            message_body={"key": "value"},
            service_name="Audio"
        )

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY
    assert "MessageId" in exc_info.value.detail


@patch("pecha_api.shared.sqs_client._get_sqs_client")
def test_send_sqs_message_client_error(mock_get_client):
    mock_client = MagicMock()
    mock_client.send_message.side_effect = ClientError(
        {"Error": {"Code": "ServiceUnavailable", "Message": "Service is down"}},
        "SendMessage"
    )
    mock_get_client.return_value = mock_client

    with pytest.raises(HTTPException) as exc_info:
        send_sqs_message(
            queue_url="https://sqs.us-east-1.amazonaws.com/123456789/test-queue",
            message_body={"key": "value"},
            service_name="Audio"
        )

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY
    assert "Failed to enqueue" in exc_info.value.detail


@patch("pecha_api.shared.sqs_client._get_sqs_client")
def test_send_sqs_message_unexpected_error(mock_get_client):
    mock_client = MagicMock()
    mock_client.send_message.side_effect = RuntimeError("Unexpected error")
    mock_get_client.return_value = mock_client

    with pytest.raises(HTTPException) as exc_info:
        send_sqs_message(
            queue_url="https://sqs.us-east-1.amazonaws.com/123456789/test-queue",
            message_body={"key": "value"},
            service_name="Chat"
        )

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY
    assert "chat" in exc_info.value.detail.lower()


@patch("pecha_api.shared.sqs_client._get_sqs_client")
def test_send_sqs_message_serializes_with_default_str(mock_get_client):
    mock_client = MagicMock()
    mock_client.send_message.return_value = {"MessageId": "test-123"}
    mock_get_client.return_value = mock_client

    from datetime import datetime
    dt = datetime(2025, 1, 1, 12, 0, 0)

    send_sqs_message(
        queue_url="https://sqs.us-east-1.amazonaws.com/123456789/test-queue",
        message_body={"timestamp": dt},
        service_name="Audio"
    )

    call_args = mock_client.send_message.call_args
    assert "2025-01-01" in call_args.kwargs["MessageBody"]
