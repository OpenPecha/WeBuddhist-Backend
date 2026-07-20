from uuid import uuid4
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from pecha_api.plans.audio.audio_generation_payload_service import (
    apply_day_audio_generation_result,
    apply_sub_task_audio_generation_result,
    get_day_audio_generation_payload,
    get_sub_task_audio_generation_payload,
)
from pecha_api.plans.audio.plan_audio_response_models import (
    DayAudioGenerationResultRequest,
    SubTaskAudioGenerationResultRequest,
    SubTaskTimestampPayload,
)
from pecha_api.plans.plans_enums import ContentType


def _mock_subtask(*, content_type=ContentType.TEXT, content="hello", audio_url=None, display_order=1):
    subtask = MagicMock()
    subtask.id = uuid4()
    subtask.task_id = uuid4()
    subtask.content_type = content_type
    subtask.content = content
    subtask.audio_url = audio_url
    subtask.display_order = display_order
    return subtask


@patch("pecha_api.plans.audio.audio_generation_payload_service.get_plan_day_by_id_any_plan")
@patch("pecha_api.plans.audio.audio_generation_payload_service.SessionLocal")
def test_get_day_audio_generation_payload_filters_and_orders(mock_session_local, mock_get_day):
    day_id = uuid4()
    plan_id = uuid4()

    text_sub = _mock_subtask(content_type=ContentType.TEXT, display_order=2)
    video_sub = _mock_subtask(content_type=ContentType.VIDEO, display_order=1)
    ref_sub = _mock_subtask(content_type=ContentType.SOURCE_REFERENCE, display_order=1)

    task_b = MagicMock()
    task_b.display_order = 2
    task_b.sub_tasks = [text_sub]

    task_a = MagicMock()
    task_a.display_order = 1
    task_a.sub_tasks = [video_sub, ref_sub]

    plan_item = MagicMock()
    plan_item.id = day_id
    plan_item.plan_id = plan_id
    plan_item.tasks = [task_b, task_a]
    mock_get_day.return_value = plan_item
    mock_session_local.return_value.__enter__.return_value = MagicMock()

    payload = get_day_audio_generation_payload(day_id=day_id)

    assert payload.id == day_id
    assert payload.plan_id == plan_id
    assert [item.id for item in payload.subtasks] == [ref_sub.id, text_sub.id]
    assert payload.subtasks[0].content_type == "SOURCE_REFERENCE"
    assert payload.subtasks[1].content_type == "TEXT"


@patch("pecha_api.plans.audio.audio_generation_payload_service.get_sub_task_by_subtask_id")
@patch("pecha_api.plans.audio.audio_generation_payload_service.SessionLocal")
def test_get_sub_task_audio_generation_payload_success(mock_session_local, mock_get_subtask):
    subtask = _mock_subtask()
    mock_get_subtask.return_value = subtask
    mock_session_local.return_value.__enter__.return_value = MagicMock()

    payload = get_sub_task_audio_generation_payload(sub_task_id=subtask.id)

    assert payload.id == subtask.id
    assert payload.task_id == subtask.task_id
    assert payload.content == "hello"
    assert payload.content_type == "TEXT"


@patch("pecha_api.plans.audio.audio_generation_payload_service.get_sub_task_by_subtask_id")
@patch("pecha_api.plans.audio.audio_generation_payload_service.SessionLocal")
def test_get_sub_task_audio_generation_payload_not_found(mock_session_local, mock_get_subtask):
    mock_get_subtask.return_value = None
    mock_session_local.return_value.__enter__.return_value = MagicMock()

    with pytest.raises(HTTPException) as exc:
        get_sub_task_audio_generation_payload(sub_task_id=uuid4())

    assert exc.value.status_code == 404


@patch("pecha_api.plans.audio.audio_generation_payload_service.get_sub_task_by_subtask_id")
@patch("pecha_api.plans.audio.audio_generation_payload_service.SessionLocal")
def test_get_sub_task_audio_generation_payload_invalid_type(mock_session_local, mock_get_subtask):
    mock_get_subtask.return_value = _mock_subtask(content_type=ContentType.VIDEO)
    mock_session_local.return_value.__enter__.return_value = MagicMock()

    with pytest.raises(HTTPException) as exc:
        get_sub_task_audio_generation_payload(sub_task_id=uuid4())

    assert exc.value.status_code == 400


@patch("pecha_api.plans.audio.audio_generation_payload_service.schedule_invalidate_plan_day_cache_for_day")
@patch("pecha_api.plans.audio.audio_generation_payload_service.upsert_plan_item_audio")
@patch("pecha_api.plans.audio.audio_generation_payload_service.upsert_sub_task_timestamp")
@patch("pecha_api.plans.audio.audio_generation_payload_service.get_plan_day_by_id_any_plan")
@patch("pecha_api.plans.audio.audio_generation_payload_service.SessionLocal")
def test_apply_day_audio_generation_result(
    mock_session_local,
    mock_get_day,
    mock_upsert_timestamp,
    mock_upsert_audio,
    mock_invalidate,
):
    day_id = uuid4()
    sub_task_id = uuid4()
    plan_item = MagicMock()
    plan_item.id = day_id
    mock_get_day.return_value = plan_item
    mock_session_local.return_value.__enter__.return_value = MagicMock()

    apply_day_audio_generation_result(
        day_id=day_id,
        request=DayAudioGenerationResultRequest(
            audio_key="audio/day.wav",
            duration_ms=1200,
            file_size_bytes=500,
            timestamps=[
                SubTaskTimestampPayload(sub_task_id=sub_task_id, start_ms=0, end_ms=1200)
            ],
        ),
    )

    mock_upsert_timestamp.assert_called_once()
    mock_upsert_audio.assert_called_once()
    mock_invalidate.assert_called_once()


@patch("pecha_api.plans.audio.audio_generation_payload_service.schedule_invalidate_plan_day_cache_for_task")
@patch("pecha_api.plans.audio.audio_generation_payload_service.upsert_sub_task_timestamp")
@patch("pecha_api.plans.audio.audio_generation_payload_service.get_sub_task_by_subtask_id")
@patch("pecha_api.plans.audio.audio_generation_payload_service.SessionLocal")
def test_apply_sub_task_audio_generation_result(
    mock_session_local,
    mock_get_subtask,
    mock_upsert_timestamp,
    mock_invalidate,
):
    subtask = _mock_subtask()
    mock_db = MagicMock()
    mock_get_subtask.return_value = subtask
    mock_session_local.return_value.__enter__.return_value = mock_db

    apply_sub_task_audio_generation_result(
        sub_task_id=subtask.id,
        request=SubTaskAudioGenerationResultRequest(
            audio_key="audio/sub.wav",
            duration_ms=900,
        ),
    )

    assert subtask.audio_url == "audio/sub.wav"
    assert subtask.duration == "900"
    mock_db.commit.assert_called_once()
    mock_upsert_timestamp.assert_called_once()
    mock_invalidate.assert_called_once()
