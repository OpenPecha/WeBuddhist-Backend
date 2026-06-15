import io
import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from fastapi import HTTPException, UploadFile

from pecha_api.plans.platform_enums import PlatformRole
from pecha_api.plans.audio.plan_subtask_audio_service import (
    _get_author_sub_task,
    delete_plan_subtask_audio,
    upload_plan_subtask_audio,
)


@patch("pecha_api.plans.audio.plan_subtask_audio_service.generate_presigned_access_url", return_value="https://audio.url")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.delete_file")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.upload_file", return_value="audio/key.mp3")
@patch("pecha_api.plans.audio.plan_subtask_audio_service._get_author_sub_task")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.validate_cms_author_details")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.SessionLocal")
def test_upload_plan_subtask_audio_success(
    mock_session,
    mock_validate,
    mock_get_subtask,
    mock_upload,
    mock_delete_file,
    mock_presign,
):
    sub_task_id = uuid4()
    task_id = uuid4()

    author = MagicMock()
    author.email = "author@test.com"
    author.platform_role = PlatformRole.SUPER_ADMIN
    mock_validate.return_value = author

    subtask = MagicMock()
    subtask.task_id = task_id
    subtask.audio_url = "audio/plan_subtasks/old.mp3"
    mock_get_subtask.return_value = subtask

    mock_db = MagicMock()
    mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
    mock_session.return_value.__exit__ = MagicMock(return_value=False)

    file = MagicMock(spec=UploadFile)
    file.filename = "subtask.mp3"
    file.content_type = "audio/mpeg"
    file.size = 1024
    file.file = io.BytesIO(b"audio")

    response = upload_plan_subtask_audio(
        token="token",
        sub_task_id=sub_task_id,
        file=file,
        duration_ms=45000,
    )

    mock_delete_file.assert_called_once_with("audio/plan_subtasks/old.mp3")
    mock_upload.assert_called_once()
    mock_db.commit.assert_called_once()
    assert response.sub_task_id == str(sub_task_id)
    assert response.task_id == str(task_id)
    assert response.audio_url == "https://audio.url"
    assert response.duration_ms == 45000
    assert response.message == "Sub task audio uploaded successfully"


@patch("pecha_api.plans.audio.plan_subtask_audio_service.delete_file")
@patch("pecha_api.plans.audio.plan_subtask_audio_service._get_author_sub_task")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.validate_cms_author_details")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.SessionLocal")
def test_delete_plan_subtask_audio_success(
    mock_session,
    mock_validate,
    mock_get_subtask,
    mock_delete_file,
):
    sub_task_id = uuid4()

    author = MagicMock()
    author.email = "author@test.com"
    mock_validate.return_value = author

    subtask = MagicMock()
    subtask.audio_url = "audio/plan_subtasks/task/sub.mp3"
    mock_get_subtask.return_value = subtask

    mock_db = MagicMock()
    mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
    mock_session.return_value.__exit__ = MagicMock(return_value=False)

    delete_plan_subtask_audio(token="token", sub_task_id=sub_task_id)

    mock_delete_file.assert_called_once_with("audio/plan_subtasks/task/sub.mp3")
    assert subtask.audio_url is None
    assert subtask.duration is None
    mock_db.commit.assert_called_once()


@patch("pecha_api.plans.audio.plan_subtask_audio_service._get_author_sub_task")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.validate_cms_author_details")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.SessionLocal")
def test_delete_plan_subtask_audio_without_existing_audio(
    mock_session,
    mock_validate,
    mock_get_subtask,
):
    mock_validate.return_value = MagicMock(email="author@test.com")

    subtask = MagicMock()
    subtask.audio_url = None
    mock_get_subtask.return_value = subtask

    mock_db = MagicMock()
    mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
    mock_session.return_value.__exit__ = MagicMock(return_value=False)

    delete_plan_subtask_audio(token="token", sub_task_id=uuid4())

    assert subtask.audio_url is None
    assert subtask.duration is None
    mock_db.commit.assert_called_once()


@patch("pecha_api.plans.audio.plan_subtask_audio_service._get_author_sub_task")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.validate_cms_author_details")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.SessionLocal")
def test_upload_plan_subtask_audio_not_found(
    mock_session,
    mock_validate,
    mock_get_subtask,
):
    mock_validate.return_value = MagicMock(email="author@test.com")
    mock_get_subtask.side_effect = HTTPException(status_code=404, detail={"error": "bad", "message": "Sub task not found"})
    mock_session.return_value.__enter__ = MagicMock(return_value=MagicMock())
    mock_session.return_value.__exit__ = MagicMock(return_value=False)

    file = MagicMock(spec=UploadFile)
    file.filename = "subtask.mp3"
    file.size = 1024
    file.file = io.BytesIO(b"audio")

    with pytest.raises(HTTPException) as exc:
        upload_plan_subtask_audio(
            token="token",
            sub_task_id=uuid4(),
            file=file,
        )
    assert exc.value.status_code == 404


def test_get_author_sub_task_success():
    db = MagicMock()
    sub_task_id = uuid4()
    task_id = uuid4()
    plan_item_id = uuid4()
    plan_id = uuid4()
    author = MagicMock(email="author@test.com")

    subtask = MagicMock()
    subtask.task_id = task_id
    task = MagicMock(plan_item_id=plan_item_id)
    plan_item = MagicMock(plan_id=plan_id)
    plan = MagicMock(group_id=uuid4(), status="draft")

    with patch(
        "pecha_api.plans.audio.plan_subtask_audio_service.get_sub_task_by_subtask_id",
        return_value=subtask,
    ) as mock_get_subtask, patch(
        "pecha_api.plans.audio.plan_subtask_audio_service.get_task_by_id",
        return_value=task,
    ) as mock_get_task, patch(
        "pecha_api.plans.audio.plan_subtask_audio_service.get_plan_item_by_id",
        return_value=plan_item,
    ) as mock_get_plan_item, patch(
        "pecha_api.plans.audio.plan_subtask_audio_service.get_plan_by_id",
        return_value=plan,
    ) as mock_get_plan, patch(
        "pecha_api.plans.audio.plan_subtask_audio_service.require_can_edit_content",
    ) as mock_require_edit:
        result = _get_author_sub_task(db=db, sub_task_id=sub_task_id, current_author=author)

        assert result == subtask
        mock_get_subtask.assert_called_once_with(db=db, id=sub_task_id)
        mock_get_task.assert_called_once_with(db=db, task_id=task_id)
        mock_get_plan_item.assert_called_once_with(db=db, day_id=plan_item_id)
        mock_get_plan.assert_called_once_with(db=db, plan_id=plan_id)
        mock_require_edit.assert_called_once_with(
            db=db,
            group_id=plan.group_id,
            author=author,
            content_status=plan.status,
        )


def test_get_author_sub_task_raises_when_subtask_missing():
    author = MagicMock(email="author@test.com")

    with patch(
        "pecha_api.plans.audio.plan_subtask_audio_service.get_sub_task_by_subtask_id",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc:
            _get_author_sub_task(db=MagicMock(), sub_task_id=uuid4(), current_author=author)

        assert exc.value.status_code == 404


def test_get_author_sub_task_raises_when_task_missing():
    author = MagicMock(email="author@test.com")
    subtask = MagicMock(task_id=uuid4())

    with patch(
        "pecha_api.plans.audio.plan_subtask_audio_service.get_sub_task_by_subtask_id",
        return_value=subtask,
    ), patch(
        "pecha_api.plans.audio.plan_subtask_audio_service.get_task_by_id",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc:
            _get_author_sub_task(db=MagicMock(), sub_task_id=uuid4(), current_author=author)

        assert exc.value.status_code == 404


def test_get_author_sub_task_raises_when_plan_day_missing():
    author = MagicMock(email="author@test.com")
    subtask = MagicMock(task_id=uuid4())

    with patch(
        "pecha_api.plans.audio.plan_subtask_audio_service.get_sub_task_by_subtask_id",
        return_value=subtask,
    ), patch(
        "pecha_api.plans.audio.plan_subtask_audio_service.get_task_by_id",
        return_value=MagicMock(plan_item_id=uuid4()),
    ), patch(
        "pecha_api.plans.audio.plan_subtask_audio_service.get_plan_item_by_id",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc:
            _get_author_sub_task(db=MagicMock(), sub_task_id=uuid4(), current_author=author)

        assert exc.value.status_code == 404


def test_get_author_sub_task_raises_when_plan_missing():
    author = MagicMock(email="author@test.com")
    subtask = MagicMock(task_id=uuid4())
    plan_item_id = uuid4()

    with patch(
        "pecha_api.plans.audio.plan_subtask_audio_service.get_sub_task_by_subtask_id",
        return_value=subtask,
    ), patch(
        "pecha_api.plans.audio.plan_subtask_audio_service.get_task_by_id",
        return_value=MagicMock(plan_item_id=plan_item_id),
    ), patch(
        "pecha_api.plans.audio.plan_subtask_audio_service.get_plan_item_by_id",
        return_value=MagicMock(plan_id=uuid4()),
    ), patch(
        "pecha_api.plans.audio.plan_subtask_audio_service.get_plan_by_id",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc:
            _get_author_sub_task(db=MagicMock(), sub_task_id=uuid4(), current_author=author)

        assert exc.value.status_code == 404


@patch("pecha_api.plans.audio.plan_subtask_audio_service.generate_presigned_access_url", return_value="https://audio.url")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.upload_file", return_value="audio/key.mp3")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.get_sub_task_by_subtask_id")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.get_task_by_id")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.get_plan_item_by_id")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.get_plan_by_id")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.require_can_edit_content")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.validate_cms_author_details")
@patch("pecha_api.plans.audio.plan_subtask_audio_service.SessionLocal")
def test_upload_plan_subtask_audio_without_duration_ms(
    mock_session,
    mock_validate,
    mock_require_edit,
    mock_get_plan,
    mock_get_plan_item,
    mock_get_task,
    mock_get_subtask,
    mock_upload,
    mock_presign,
):
    sub_task_id = uuid4()
    task_id = uuid4()
    plan_item_id = uuid4()
    plan_id = uuid4()

    author = MagicMock()
    author.email = "author@test.com"
    mock_validate.return_value = author

    subtask = MagicMock()
    subtask.task_id = task_id
    subtask.audio_url = None
    mock_get_subtask.return_value = subtask
    mock_get_task.return_value = MagicMock(plan_item_id=plan_item_id)
    mock_get_plan_item.return_value = MagicMock(plan_id=plan_id)
    mock_get_plan.return_value = MagicMock(group_id=uuid4(), status="draft")

    mock_db = MagicMock()
    mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
    mock_session.return_value.__exit__ = MagicMock(return_value=False)

    file = MagicMock(spec=UploadFile)
    file.filename = "subtask.mp3"
    file.content_type = "audio/mpeg"
    file.size = 1024
    file.file = io.BytesIO(b"audio")

    response = upload_plan_subtask_audio(
        token="token",
        sub_task_id=sub_task_id,
        file=file,
    )

    assert response.duration_ms is None
    assert subtask.duration is None
    mock_require_edit.assert_called_once()
