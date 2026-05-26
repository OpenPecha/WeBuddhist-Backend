import io
import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from fastapi import HTTPException, UploadFile

from pecha_api.plans.audio.plan_day_audio_service import (
    _validate_audio_file,
    upload_plan_day_audio,
)


def test_validate_audio_file_rejects_invalid_extension():
    file = MagicMock(spec=UploadFile)
    file.filename = "track.exe"
    file.size = 1000
    with pytest.raises(HTTPException) as exc:
        _validate_audio_file(file)
    assert exc.value.status_code == 400


@patch("pecha_api.plans.audio.plan_day_audio_service.generate_presigned_access_url", return_value="https://audio.url")
@patch("pecha_api.plans.audio.plan_day_audio_service.upsert_plan_item_audio")
@patch("pecha_api.plans.audio.plan_day_audio_service.get_plan_item_audio_by_plan_item_id", return_value=None)
@patch("pecha_api.plans.audio.plan_day_audio_service.upload_file", return_value="audio/key.mp3")
@patch("pecha_api.plans.audio.plan_day_audio_service._get_author_plan_item_by_day_id")
@patch("pecha_api.plans.audio.plan_day_audio_service.validate_and_extract_author_details")
@patch("pecha_api.plans.audio.plan_day_audio_service.SessionLocal")
def test_upload_plan_day_audio_success(
    mock_session,
    mock_validate,
    mock_get_item,
    mock_upload,
    mock_get_existing,
    mock_upsert,
    mock_presign,
):
    plan_id = uuid4()
    day_id = uuid4()
    plan_item_id = day_id

    author = MagicMock()
    author.email = "author@test.com"
    author.is_admin = True
    mock_validate.return_value = author

    plan_item = MagicMock()
    plan_item.id = plan_item_id
    plan_item.plan_id = plan_id
    mock_get_item.return_value = plan_item

    audio_row = MagicMock()
    audio_row.audio_key = "audio/key.mp3"
    audio_row.duration_ms = 120000
    mock_upsert.return_value = audio_row

    mock_session.return_value.__enter__ = MagicMock(return_value=MagicMock())
    mock_session.return_value.__exit__ = MagicMock(return_value=False)

    file = MagicMock(spec=UploadFile)
    file.filename = "day.mp3"
    file.content_type = "audio/mpeg"
    file.size = 1024
    file.file = io.BytesIO(b"audio")

    response = upload_plan_day_audio(
        token="token",
        day_id=day_id,
        file=file,
        duration_ms=120000,
    )

    assert response.audio_key == "audio/key.mp3"
    assert response.audio_url == "https://audio.url"
    assert response.duration_ms == 120000
