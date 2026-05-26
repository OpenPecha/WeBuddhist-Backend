import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from fastapi import HTTPException

from pecha_api.plans.audio.timestamp_service import (
    validate_timestamp_pair,
    validate_timestamp_range,
    apply_sub_task_timestamp,
)


def test_validate_timestamp_pair_rejects_only_start():
    with pytest.raises(HTTPException) as exc:
        validate_timestamp_pair(start_ms=0, end_ms=None)
    assert exc.value.status_code == 400


def test_validate_timestamp_pair_rejects_only_end():
    with pytest.raises(HTTPException) as exc:
        validate_timestamp_pair(start_ms=None, end_ms=100)
    assert exc.value.status_code == 400


def test_validate_timestamp_range_rejects_end_before_start():
    with pytest.raises(HTTPException) as exc:
        validate_timestamp_range(start_ms=100, end_ms=50, duration_ms=None)
    assert exc.value.status_code == 400


def test_validate_timestamp_range_rejects_end_beyond_duration():
    with pytest.raises(HTTPException) as exc:
        validate_timestamp_range(start_ms=0, end_ms=5000, duration_ms=1000)
    assert exc.value.status_code == 400


@patch("pecha_api.plans.audio.timestamp_service.upsert_sub_task_timestamp")
@patch("pecha_api.plans.audio.timestamp_service.get_day_audio_duration_ms", return_value=60000)
def test_apply_sub_task_timestamp_upserts(mock_duration, mock_upsert):
    db = MagicMock()
    sub_task_id = uuid4()
    task_id = uuid4()
    mock_upsert.return_value = MagicMock(start_ms=0, end_ms=1000)

    start, end = apply_sub_task_timestamp(
        db=db,
        sub_task_id=sub_task_id,
        task_id=task_id,
        start_ms=0,
        end_ms=1000,
        author_email="author@test.com",
    )

    assert start == 0
    assert end == 1000
    mock_upsert.assert_called_once()


@patch("pecha_api.plans.audio.timestamp_service.delete_sub_task_timestamp")
def test_apply_sub_task_timestamp_clears_when_omitted(mock_delete):
    db = MagicMock()
    start, end = apply_sub_task_timestamp(
        db=db,
        sub_task_id=uuid4(),
        task_id=uuid4(),
        start_ms=None,
        end_ms=None,
        author_email="author@test.com",
    )

    assert start is None and end is None
    mock_delete.assert_called_once()
