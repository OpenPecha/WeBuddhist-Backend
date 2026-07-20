import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from pecha_api.plans.audio.audio_job_models import AudioJob
from pecha_api.plans.audio.audio_job_service import enqueue_plan_audio_job, get_audio_job_status
from pecha_api.plans.audio.sqs_client import send_audio_job_message, is_audio_sqs_configured
from pecha_api.plans.plans_enums import AudioJobStatus, ContentType, MonlamVoiceName, PlanAudioType


def test_is_audio_sqs_configured_true():
    with patch("pecha_api.plans.audio.sqs_client.get", return_value="https://sqs.example.com/queue"):
        assert is_audio_sqs_configured() is True


def test_is_audio_sqs_configured_false_for_blank():
    with patch("pecha_api.plans.audio.sqs_client.get", return_value="  "):
        assert is_audio_sqs_configured() is False


def test_send_audio_job_message_success():
    mock_client = MagicMock()
    mock_client.send_message.return_value = {"MessageId": "msg-123"}

    with patch("pecha_api.plans.audio.sqs_client.get", side_effect=lambda key: {
        "AUDIO_SQS_QUEUE_URL": "https://sqs.example.com/queue",
        "AWS_ACCESS_KEY": "key",
        "AWS_SECRET_KEY": "secret",
        "AWS_REGION": "eu-central-1",
    }.get(key, "")), \
         patch("pecha_api.plans.audio.sqs_client._get_sqs_client", return_value=mock_client):
        message_id = send_audio_job_message({"job_id": "abc"})

    assert message_id == "msg-123"
    mock_client.send_message.assert_called_once()


def test_send_audio_job_message_requires_queue_url():
    with patch("pecha_api.plans.audio.sqs_client.get", return_value=""):
        with pytest.raises(HTTPException) as exc:
            send_audio_job_message({"job_id": "abc"})
    assert exc.value.status_code == 503


@patch("pecha_api.plans.audio.audio_job_service.send_audio_job_message", return_value="msg-1")
@patch("pecha_api.plans.audio.audio_job_service.update_audio_job_sqs_message_id")
@patch("pecha_api.plans.audio.audio_job_service.create_audio_job")
@patch("pecha_api.plans.audio.audio_job_service._validate_audio_job_target")
@patch("pecha_api.plans.audio.audio_job_service.SessionLocal")
def test_enqueue_plan_audio_job_success(
    mock_session_local,
    mock_validate,
    mock_create,
    mock_update_message,
    mock_send,
):
    job_id = uuid.uuid4()
    day_id = uuid.uuid4()
    job = AudioJob(
        id=job_id,
        status=AudioJobStatus.PENDING.value,
        day_id=day_id,
        language="bo",
        audio_type=PlanAudioType.TEXT_READING.value,
        voice_name=MonlamVoiceName.DOLKAR_LHASA_FEMALE.value,
        payload={},
    )
    mock_create.return_value = job
    mock_session_local.return_value.__enter__.return_value = MagicMock()

    result = enqueue_plan_audio_job(
        language="bo",
        day_id=day_id,
        audio_type=PlanAudioType.TEXT_READING,
        voice_name=MonlamVoiceName.DOLKAR_LHASA_FEMALE,
    )

    assert result.job_id == job_id
    assert result.status == AudioJobStatus.PENDING
    mock_validate.assert_called_once()
    mock_send.assert_called_once()
    mock_update_message.assert_called_once()
    payload = mock_send.call_args.args[0]
    assert payload["job_id"] == str(job_id)
    assert payload["day_id"] == str(day_id)
    assert payload["language"] == "bo"


@patch("pecha_api.plans.audio.audio_job_service.mark_audio_job_failed")
@patch(
    "pecha_api.plans.audio.audio_job_service.send_audio_job_message",
    side_effect=HTTPException(status_code=502, detail="Failed to enqueue audio generation job"),
)
@patch("pecha_api.plans.audio.audio_job_service.create_audio_job")
@patch("pecha_api.plans.audio.audio_job_service._validate_audio_job_target")
@patch("pecha_api.plans.audio.audio_job_service.SessionLocal")
def test_enqueue_plan_audio_job_marks_failed_when_sqs_fails(
    mock_session_local,
    mock_validate,
    mock_create,
    mock_send,
    mock_mark_failed,
):
    job_id = uuid.uuid4()
    job = AudioJob(
        id=job_id,
        status=AudioJobStatus.PENDING.value,
        day_id=uuid.uuid4(),
        language="bo",
        audio_type=PlanAudioType.TEXT_READING.value,
        voice_name=MonlamVoiceName.DOLKAR_LHASA_FEMALE.value,
        payload={},
    )
    mock_create.return_value = job
    mock_session_local.return_value.__enter__.return_value = MagicMock()

    with pytest.raises(HTTPException) as exc:
        enqueue_plan_audio_job(language="bo", day_id=uuid.uuid4())

    assert exc.value.status_code == 502
    mock_mark_failed.assert_called_once()
    assert mock_mark_failed.call_args.kwargs["job_id"] == job_id


@patch("pecha_api.plans.audio.audio_job_service.generate_presigned_access_url", return_value="https://presigned")
@patch("pecha_api.plans.audio.audio_job_service.get", return_value="bucket")
@patch("pecha_api.plans.audio.audio_job_service.get_audio_job_by_id")
@patch("pecha_api.plans.audio.audio_job_service.SessionLocal")
def test_get_audio_job_status_completed(
    mock_session_local,
    mock_get_job,
    mock_get,
    mock_presign,
):
    job_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    job = AudioJob(
        id=job_id,
        status=AudioJobStatus.COMPLETED.value,
        day_id=uuid.uuid4(),
        language="bo",
        audio_type=PlanAudioType.TEXT_READING.value,
        voice_name=MonlamVoiceName.DOLKAR_LHASA_FEMALE.value,
        payload={},
        result={"s3_key": "audio/day.wav", "audio_duration_ms": 1200},
        created_at=now,
        updated_at=now,
        completed_at=now,
    )
    mock_get_job.return_value = job
    mock_session_local.return_value.__enter__.return_value = MagicMock()

    result = get_audio_job_status(job_id=job_id)

    assert result.job_id == job_id
    assert result.status == AudioJobStatus.COMPLETED
    assert result.audio_url == "https://presigned"
    assert result.audio_duration_ms == 1200
    assert result.s3_key == "audio/day.wav"


@patch("pecha_api.plans.audio.audio_job_service.get_audio_job_by_id", return_value=None)
@patch("pecha_api.plans.audio.audio_job_service.SessionLocal")
def test_get_audio_job_status_not_found(mock_session_local, mock_get_job):
    mock_session_local.return_value.__enter__.return_value = MagicMock()
    with pytest.raises(HTTPException) as exc:
        get_audio_job_status(job_id=uuid.uuid4())
    assert exc.value.status_code == 404


@patch("pecha_api.plans.audio.audio_job_service.mark_audio_job_processing")
@patch("pecha_api.plans.audio.audio_job_service.get_audio_job_by_id")
@patch("pecha_api.plans.audio.audio_job_service.SessionLocal")
def test_update_audio_job_status_processing(
    mock_session_local,
    mock_get_job,
    mock_mark_processing,
):
    from pecha_api.plans.audio.audio_job_service import update_audio_job_status

    job_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    pending = AudioJob(
        id=job_id,
        status=AudioJobStatus.PENDING.value,
        day_id=uuid.uuid4(),
        language="bo",
        audio_type=PlanAudioType.TEXT_READING.value,
        voice_name=MonlamVoiceName.DOLKAR_LHASA_FEMALE.value,
        payload={},
        created_at=now,
        updated_at=now,
    )
    processing = AudioJob(
        id=job_id,
        status=AudioJobStatus.PROCESSING.value,
        day_id=pending.day_id,
        language="bo",
        audio_type=PlanAudioType.TEXT_READING.value,
        voice_name=MonlamVoiceName.DOLKAR_LHASA_FEMALE.value,
        payload={},
        created_at=now,
        updated_at=now,
        started_at=now,
    )
    mock_get_job.return_value = pending
    mock_mark_processing.return_value = processing
    mock_session_local.return_value.__enter__.return_value = MagicMock()

    result = update_audio_job_status(job_id=job_id, next_status=AudioJobStatus.PROCESSING)

    assert result.status == AudioJobStatus.PROCESSING
    mock_mark_processing.assert_called_once()


@patch("pecha_api.plans.audio.audio_job_service.mark_audio_job_completed")
@patch("pecha_api.plans.audio.audio_job_service.get_audio_job_by_id")
@patch("pecha_api.plans.audio.audio_job_service.SessionLocal")
def test_update_audio_job_status_completed(
    mock_session_local,
    mock_get_job,
    mock_mark_completed,
):
    from pecha_api.plans.audio.audio_job_service import update_audio_job_status

    job_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    processing = AudioJob(
        id=job_id,
        status=AudioJobStatus.PROCESSING.value,
        day_id=uuid.uuid4(),
        language="bo",
        audio_type=PlanAudioType.TEXT_READING.value,
        voice_name=MonlamVoiceName.DOLKAR_LHASA_FEMALE.value,
        payload={},
        created_at=now,
        updated_at=now,
        started_at=now,
    )
    completed = AudioJob(
        id=job_id,
        status=AudioJobStatus.COMPLETED.value,
        day_id=processing.day_id,
        language="bo",
        audio_type=PlanAudioType.TEXT_READING.value,
        voice_name=MonlamVoiceName.DOLKAR_LHASA_FEMALE.value,
        payload={},
        result={"s3_key": "audio/day.wav", "audio_duration_ms": 1000},
        created_at=now,
        updated_at=now,
        started_at=now,
        completed_at=now,
    )
    mock_get_job.return_value = processing
    mock_mark_completed.return_value = completed
    mock_session_local.return_value.__enter__.return_value = MagicMock()

    with patch(
        "pecha_api.plans.audio.audio_job_service.generate_presigned_access_url",
        return_value="https://presigned",
    ), patch("pecha_api.plans.audio.audio_job_service.get", return_value="bucket"):
        result = update_audio_job_status(
            job_id=job_id,
            next_status=AudioJobStatus.COMPLETED,
            result={"s3_key": "audio/day.wav", "audio_duration_ms": 1000},
        )

    assert result.status == AudioJobStatus.COMPLETED
    assert result.s3_key == "audio/day.wav"
    mock_mark_completed.assert_called_once()


@patch("pecha_api.plans.audio.audio_job_service.mark_audio_job_processing")
@patch("pecha_api.plans.audio.audio_job_service.get_audio_job_by_id")
@patch("pecha_api.plans.audio.audio_job_service.SessionLocal")
def test_update_audio_job_status_noop_when_terminal(
    mock_session_local,
    mock_get_job,
    mock_mark_processing,
):
    from pecha_api.plans.audio.audio_job_service import update_audio_job_status

    job_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    completed = AudioJob(
        id=job_id,
        status=AudioJobStatus.COMPLETED.value,
        day_id=uuid.uuid4(),
        language="bo",
        audio_type=PlanAudioType.TEXT_READING.value,
        voice_name=MonlamVoiceName.DOLKAR_LHASA_FEMALE.value,
        payload={},
        result={"s3_key": "audio/day.wav"},
        created_at=now,
        updated_at=now,
        completed_at=now,
    )
    mock_get_job.return_value = completed
    mock_session_local.return_value.__enter__.return_value = MagicMock()

    with patch(
        "pecha_api.plans.audio.audio_job_service.generate_presigned_access_url",
        return_value="https://presigned",
    ), patch("pecha_api.plans.audio.audio_job_service.get", return_value="bucket"):
        result = update_audio_job_status(job_id=job_id, next_status=AudioJobStatus.PROCESSING)

    assert result.status == AudioJobStatus.COMPLETED
    mock_mark_processing.assert_not_called()


@patch("pecha_api.plans.audio.audio_job_service.get_sub_task_by_subtask_id")
@patch("pecha_api.plans.audio.audio_job_service.SessionLocal")
def test_enqueue_rejects_non_text_subtask(mock_session_local, mock_get_subtask):
    from pecha_api.plans.audio.audio_job_service import _validate_audio_job_target

    subtask = MagicMock()
    subtask.content_type = ContentType.VIDEO
    mock_get_subtask.return_value = subtask
    mock_session_local.return_value.__enter__.return_value = MagicMock()

    with pytest.raises(HTTPException) as exc:
        _validate_audio_job_target(day_id=None, sub_task_id=uuid.uuid4())
    assert exc.value.status_code == 400
