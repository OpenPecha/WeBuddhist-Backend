import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from fastapi import HTTPException

from pecha_api.plans.audio.timestamp_service import (
    validate_timestamp_pair,
    validate_timestamp_range,
    apply_sub_task_timestamp,
    get_day_audio_duration_ms,
    timestamp_fields_from_subtask,
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


def test_validate_timestamp_pair_accepts_both_omitted():
    validate_timestamp_pair(start_ms=None, end_ms=None)


def test_validate_timestamp_pair_accepts_both_provided():
    validate_timestamp_pair(start_ms=0, end_ms=1000)


def test_validate_timestamp_range_accepts_valid_range():
    validate_timestamp_range(start_ms=0, end_ms=1000, duration_ms=5000)


@patch("pecha_api.plans.audio.timestamp_service.get_plan_item_audio_by_plan_item_id")
@patch("pecha_api.plans.audio.timestamp_service.get_task_by_id")
def test_get_day_audio_duration_ms_returns_duration(mock_get_task, mock_get_audio):
    db = MagicMock()
    task_id = uuid4()
    plan_item_id = uuid4()
    mock_get_task.return_value = MagicMock(plan_item_id=plan_item_id)
    mock_get_audio.return_value = MagicMock(duration_ms=120000)

    duration_ms = get_day_audio_duration_ms(db=db, task_id=task_id)

    assert duration_ms == 120000
    mock_get_task.assert_called_once_with(db=db, task_id=task_id)
    mock_get_audio.assert_called_once_with(db=db, plan_item_id=plan_item_id)


@patch("pecha_api.plans.audio.timestamp_service.get_task_by_id", return_value=None)
def test_get_day_audio_duration_ms_returns_none_when_task_missing(mock_get_task):
    duration_ms = get_day_audio_duration_ms(db=MagicMock(), task_id=uuid4())

    assert duration_ms is None
    mock_get_task.assert_called_once()


@patch("pecha_api.plans.audio.timestamp_service.get_plan_item_audio_by_plan_item_id", return_value=None)
@patch("pecha_api.plans.audio.timestamp_service.get_task_by_id")
def test_get_day_audio_duration_ms_returns_none_when_audio_missing(mock_get_task, mock_get_audio):
    mock_get_task.return_value = MagicMock(plan_item_id=uuid4())

    duration_ms = get_day_audio_duration_ms(db=MagicMock(), task_id=uuid4())

    assert duration_ms is None
    mock_get_audio.assert_called_once()


def test_timestamp_fields_from_subtask_without_timestamp():
    start_ms, end_ms = timestamp_fields_from_subtask(MagicMock(timestamp=None))

    assert start_ms is None
    assert end_ms is None


def test_timestamp_fields_from_subtask_with_invalid_types():
    subtask = MagicMock()
    subtask.timestamp = MagicMock(start_ms="0", end_ms=500)

    start_ms, end_ms = timestamp_fields_from_subtask(subtask)

    assert start_ms is None
    assert end_ms is None


def test_timestamp_fields_from_subtask_with_valid_timestamp():
    subtask = MagicMock()
    subtask.timestamp = MagicMock(start_ms=100, end_ms=500)

    start_ms, end_ms = timestamp_fields_from_subtask(subtask)

    assert start_ms == 100
    assert end_ms == 500


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


@patch("pecha_api.plans.audio.timestamp_service.delete_sub_task_timestamp")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.require_can_edit_content")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.get_plan_by_id")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.get_plan_item_by_id")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.get_task_by_id")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.get_sub_task_by_subtask_id")
@patch("pecha_api.plans.audio.timestamp_service.validate_cms_author_details")
@patch("pecha_api.plans.audio.timestamp_service.SessionLocal")
def test_delete_plan_subtask_timestamp_with_author_lookup(
    mock_session,
    mock_validate,
    mock_get_subtask,
    mock_get_task,
    mock_get_plan_item,
    mock_get_plan,
    mock_require_edit,
    mock_delete_timestamp,
):
    sub_task_id = uuid4()
    task_id = uuid4()
    plan_item_id = uuid4()
    plan_id = uuid4()

    author = MagicMock(email="author@test.com")
    mock_validate.return_value = author

    subtask = MagicMock(task_id=task_id)
    mock_get_subtask.return_value = subtask
    mock_get_task.return_value = MagicMock(plan_item_id=plan_item_id)
    mock_get_plan_item.return_value = MagicMock(plan_id=plan_id)
    mock_get_plan.return_value = MagicMock(group_id=uuid4(), status="draft")

    mock_db = MagicMock()
    mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
    mock_session.return_value.__exit__ = MagicMock(return_value=False)

    from pecha_api.plans.audio.timestamp_service import delete_plan_subtask_timestamp

    delete_plan_subtask_timestamp(token="token", sub_task_id=sub_task_id)

    mock_require_edit.assert_called_once()
    mock_delete_timestamp.assert_called_once_with(db=mock_db, sub_task_id=sub_task_id)


@patch("pecha_api.plans.audio.timestamp_service.delete_sub_task_timestamp")
@patch("pecha_api.plans.audio.timestamp_service._get_author_sub_task")
@patch("pecha_api.plans.audio.timestamp_service.validate_cms_author_details")
@patch("pecha_api.plans.audio.timestamp_service.SessionLocal")
def test_delete_plan_subtask_timestamp_success(
    mock_session,
    mock_validate,
    mock_get_subtask,
    mock_delete_timestamp,
):
    sub_task_id = uuid4()

    author = MagicMock()
    author.email = "author@test.com"
    mock_validate.return_value = author
    mock_get_subtask.return_value = MagicMock()

    mock_db = MagicMock()
    mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
    mock_session.return_value.__exit__ = MagicMock(return_value=False)

    from pecha_api.plans.audio.timestamp_service import delete_plan_subtask_timestamp

    delete_plan_subtask_timestamp(token="token", sub_task_id=sub_task_id)

    mock_get_subtask.assert_called_once_with(
        db=mock_db,
        sub_task_id=sub_task_id,
        current_author=author,
    )
    mock_delete_timestamp.assert_called_once_with(db=mock_db, sub_task_id=sub_task_id)
