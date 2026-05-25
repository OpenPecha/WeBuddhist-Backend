from unittest.mock import MagicMock, patch
from uuid import uuid4

from pecha_api.plans.audio.dto_helpers import (
    build_plan_day_audio_fields,
    build_subtask_timestamp_fields,
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


def test_build_plan_day_audio_fields_without_audio():
    plan_item = MagicMock()
    plan_item.audio = None

    audio_url, duration_ms, audio_key, has_audio = build_plan_day_audio_fields(plan_item)

    assert audio_url is None
    assert duration_ms is None
    assert audio_key is None
    assert has_audio is False


def test_build_subtask_timestamp_fields():
    subtask = MagicMock()
    subtask.timestamp = MagicMock(start_ms=100, end_ms=500)

    start_ms, end_ms = build_subtask_timestamp_fields(subtask)

    assert start_ms == 100
    assert end_ms == 500
