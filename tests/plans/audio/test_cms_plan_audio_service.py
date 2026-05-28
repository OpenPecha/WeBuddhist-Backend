import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from pecha_api.plans.audio.cms_plan_audio_service import get_cms_plan_audio_list


def _make_author(*, is_admin: bool = False):
    author = MagicMock()
    author.id = uuid.uuid4()
    author.email = "author@example.com"
    author.is_admin = is_admin
    return author


def _make_audio_row(audio_key: str):
    audio = MagicMock()
    audio.id = uuid.uuid4()
    audio.audio_key = audio_key
    audio.duration_ms = 120000
    audio.mime_type = "audio/mpeg"
    audio.file_size_bytes = 1024
    audio.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return audio


def _make_plan_item(plan_id=None, day_number=1):
    plan_item = MagicMock()
    plan_item.id = uuid.uuid4()
    plan_item.plan_id = plan_id or uuid.uuid4()
    plan_item.day_number = day_number
    return plan_item


def test_get_cms_plan_audio_list_maps_rows_and_pagination():
    author = _make_author()
    plan_id = uuid.uuid4()
    audio_key = f"audio/plan_days/{plan_id}/{uuid.uuid4()}/recording.mp3"
    audio_row = _make_audio_row(audio_key)
    plan_item = _make_plan_item(plan_id=plan_id, day_number=3)
    plan = MagicMock()

    with patch(
        "pecha_api.plans.audio.cms_plan_audio_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.audio.cms_plan_audio_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.audio.cms_plan_audio_service.get_plan_item_audio_paginated",
        return_value=([(audio_row, plan_item, plan)], 1),
    ) as mock_repo, patch(
        "pecha_api.plans.audio.cms_plan_audio_service.generate_presigned_access_url",
        return_value="https://audio.example.com/signed",
    ):
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_session.return_value.__exit__.return_value = False

        response = get_cms_plan_audio_list(
            token="token",
            search="recording",
            skip=0,
            limit=10,
        )

    mock_repo.assert_called_once_with(
        db=mock_db,
        search="recording",
        author_id=author.id,
        is_admin=False,
        skip=0,
        limit=10,
    )
    assert response.total == 1
    assert response.skip == 0
    assert response.limit == 10
    assert len(response.audio) == 1
    item = response.audio[0]
    assert item.audio_key == audio_key
    assert item.file_name == "recording.mp3"
    assert item.audio_url == "https://audio.example.com/signed"
    assert item.plan_id == plan_id
    assert item.day_number == 3
    assert item.duration_ms == 120000


def test_get_cms_plan_audio_list_admin_passes_is_admin():
    author = _make_author(is_admin=True)

    with patch(
        "pecha_api.plans.audio.cms_plan_audio_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.audio.cms_plan_audio_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.audio.cms_plan_audio_service.get_plan_item_audio_paginated",
        return_value=([], 0),
    ) as mock_repo, patch(
        "pecha_api.plans.audio.cms_plan_audio_service.generate_presigned_access_url",
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_session.return_value.__exit__.return_value = False

        response = get_cms_plan_audio_list(token="token", search=None, skip=5, limit=20)

    mock_repo.assert_called_once()
    assert mock_repo.call_args.kwargs["is_admin"] is True
    assert response.total == 0
    assert response.skip == 5
    assert response.limit == 20
