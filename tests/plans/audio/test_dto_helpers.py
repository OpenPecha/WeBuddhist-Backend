from unittest.mock import MagicMock, patch

from pecha_api.plans.audio.dto_helpers import (
    build_plan_day_audio_fields,
    build_plan_day_shareable_image_fields,
    build_subtask_timestamp_fields,
    generate_subtask_content_url,
)
from pecha_api.plans.plans_enums import ContentType


@patch("pecha_api.plans.audio.dto_helpers.generate_presigned_access_url", return_value="https://signed.url")
def test_build_plan_day_audio_fields_with_audio(mock_presign):
    plan_item = MagicMock()
    plan_item.audio = MagicMock(audio_key="audio/day.mp3", duration_ms=90000)

    audio_url, duration_ms, audio_key, has_audio = build_plan_day_audio_fields(plan_item)

    assert audio_url == "https://signed.url"
    assert duration_ms == 90000
    assert audio_key == "audio/day.mp3"
    assert has_audio is True
    mock_presign.assert_called_once()


def test_build_plan_day_audio_fields_without_audio():
    plan_item = MagicMock()
    plan_item.audio = None

    audio_url, duration_ms, audio_key, has_audio = build_plan_day_audio_fields(plan_item)

    assert audio_url is None
    assert duration_ms is None
    assert audio_key is None
    assert has_audio is False


def test_build_plan_day_audio_fields_with_empty_audio_key():
    plan_item = MagicMock()
    plan_item.audio = MagicMock(audio_key="", duration_ms=90000)

    audio_url, duration_ms, audio_key, has_audio = build_plan_day_audio_fields(plan_item)

    assert audio_url is None
    assert duration_ms is None
    assert audio_key is None
    assert has_audio is False


def test_build_plan_day_audio_fields_with_invalid_audio_key_type():
    plan_item = MagicMock()
    plan_item.audio = MagicMock(audio_key=123, duration_ms=90000)

    audio_url, duration_ms, audio_key, has_audio = build_plan_day_audio_fields(plan_item)

    assert audio_url is None
    assert duration_ms is None
    assert audio_key is None
    assert has_audio is False


@patch("pecha_api.plans.audio.dto_helpers.generate_presigned_access_url")
def test_build_plan_day_shareable_image_fields_with_all_images(mock_presign):
    mock_presign.side_effect = ["https://thumbnail.url", "https://image.url"]

    shareable_images = MagicMock(
        thumbnail_key="images/thumbnail.png",
        shareable_image_key="images/shareable.png"
    )

    thumbnail_url, thumbnail_key, image_url, image_key = build_plan_day_shareable_image_fields(shareable_images)

    assert thumbnail_url == "https://thumbnail.url"
    assert thumbnail_key == "images/thumbnail.png"
    assert image_url == "https://image.url"
    assert image_key == "images/shareable.png"
    assert mock_presign.call_count == 2


@patch("pecha_api.plans.audio.dto_helpers.generate_presigned_access_url")
def test_build_plan_day_shareable_image_fields_partial_images(mock_presign):
    mock_presign.return_value = "https://signed.url"

    shareable_images = MagicMock(
        thumbnail_key="images/thumbnail.png",
        shareable_image_key=None
    )

    thumbnail_url, thumbnail_key, image_url, image_key = build_plan_day_shareable_image_fields(shareable_images)

    assert thumbnail_url == "https://signed.url"
    assert thumbnail_key == "images/thumbnail.png"
    assert image_url is None
    assert image_key is None


def test_build_plan_day_shareable_image_fields_none():
    result = build_plan_day_shareable_image_fields(None)

    assert result == (None, None, None, None)


def test_build_plan_day_shareable_image_fields_no_keys():
    shareable_images = MagicMock(
        thumbnail_key=None,
        shareable_image_key=None
    )

    thumbnail_url, thumbnail_key, image_url, image_key = build_plan_day_shareable_image_fields(shareable_images)

    assert thumbnail_url is None
    assert thumbnail_key is None
    assert image_url is None
    assert image_key is None


def test_build_subtask_timestamp_fields():
    subtask = MagicMock()
    subtask.timestamp = MagicMock(start_ms=100, end_ms=500)

    start_ms, end_ms = build_subtask_timestamp_fields(subtask)

    assert start_ms == 100
    assert end_ms == 500


def test_build_subtask_timestamp_fields_none():
    subtask = MagicMock()
    subtask.timestamp = None

    start_ms, end_ms = build_subtask_timestamp_fields(subtask)

    assert start_ms is None
    assert end_ms is None


@patch("pecha_api.plans.audio.dto_helpers.generate_presigned_access_url", return_value="https://signed.url")
def test_generate_subtask_content_url_image(mock_presign):
    url = generate_subtask_content_url(ContentType.IMAGE, "images/content.png")

    assert url == "https://signed.url"
    mock_presign.assert_called_once()


@patch("pecha_api.plans.audio.dto_helpers.generate_presigned_access_url")
def test_generate_subtask_content_url_text(mock_presign):
    url = generate_subtask_content_url(ContentType.TEXT, "Some text content")

    assert url == "Some text content"
    mock_presign.assert_not_called()


def test_generate_subtask_content_url_empty_content():
    url = generate_subtask_content_url(ContentType.TEXT, "")

    assert url == ""


@patch("pecha_api.plans.audio.dto_helpers.generate_presigned_access_url")
def test_generate_subtask_content_url_image_empty_key(mock_presign):
    url = generate_subtask_content_url(ContentType.IMAGE, "")

    assert url == ""
    mock_presign.assert_not_called()
