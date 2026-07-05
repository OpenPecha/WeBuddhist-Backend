import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from pecha_api.texts.first_segment_preview_service import (
    build_first_segment_preview_for_text,
)
from pecha_api.texts.texts_toc_utils import combine_segment_preview_contents


def test_combine_segment_preview_contents_joins_non_empty_segments():
    assert combine_segment_preview_contents(["Verse 1", "Verse 2", "Verse 3"]) == (
        "Verse 1\nVerse 2\nVerse 3"
    )


@pytest.mark.asyncio
async def test_build_first_segment_preview_for_text_combines_first_three_segments():
    text_id = str(uuid.uuid4())
    first_segment_id = uuid.uuid4()
    second_segment_id = uuid.uuid4()
    third_segment_id = uuid.uuid4()

    mock_segments = [
        SimpleNamespace(id=first_segment_id, content="Verse 1"),
        SimpleNamespace(id=second_segment_id, content="Verse 2"),
        SimpleNamespace(id=third_segment_id, content="Verse 3"),
    ]

    with patch(
        "pecha_api.texts.first_segment_preview_service.get_contents_by_id",
        new_callable=AsyncMock,
        return_value=[],
    ), patch(
        "pecha_api.texts.first_segment_preview_service.Segment.get_segments_by_text_id",
        new_callable=AsyncMock,
        return_value=mock_segments,
    ):
        segment_id, preview_content = await build_first_segment_preview_for_text(text_id)

    assert segment_id == str(first_segment_id)
    assert preview_content == "Verse 1\nVerse 2\nVerse 3"
