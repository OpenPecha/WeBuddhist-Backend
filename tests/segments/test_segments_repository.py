from unittest.mock import AsyncMock, patch

import pytest
from beanie.exceptions import CollectionWasNotInitialized

from pecha_api.texts.segments.segments_models import Segment
from pecha_api.texts.segments.segments_repository import (
    get_segment_contents_by_ids,
    get_version_translation_contents_by_parent_ids,
)


@pytest.mark.asyncio
async def test_get_segment_contents_by_ids_success():
    expected = {"seg-1": ("text-1", "content-1")}

    with patch.object(
        Segment,
        "get_segment_contents_by_ids",
        new_callable=AsyncMock,
        return_value=expected,
    ) as mock_get_contents:
        result = await get_segment_contents_by_ids(["seg-1"])

    assert result == expected
    mock_get_contents.assert_awaited_once_with(segment_ids=["seg-1"])


@pytest.mark.asyncio
async def test_get_segment_contents_by_ids_collection_not_initialized():
    with patch.object(
        Segment,
        "get_segment_contents_by_ids",
        new_callable=AsyncMock,
        side_effect=CollectionWasNotInitialized("segments"),
    ):
        result = await get_segment_contents_by_ids(["seg-1"])

    assert result == {}


@pytest.mark.asyncio
async def test_get_version_translation_contents_by_parent_ids_success():
    expected = {"parent-seg-1": "translation content"}

    with patch.object(
        Segment,
        "get_version_translation_contents_by_parent_ids",
        new_callable=AsyncMock,
        return_value=expected,
    ) as mock_get_translations:
        result = await get_version_translation_contents_by_parent_ids(
            parent_segment_ids=["parent-seg-1"],
            version_text_id="version-text-1",
        )

    assert result == expected
    mock_get_translations.assert_awaited_once_with(
        parent_segment_ids=["parent-seg-1"],
        version_text_id="version-text-1",
    )


@pytest.mark.asyncio
async def test_get_version_translation_contents_by_parent_ids_collection_not_initialized():
    with patch.object(
        Segment,
        "get_version_translation_contents_by_parent_ids",
        new_callable=AsyncMock,
        side_effect=CollectionWasNotInitialized("segments"),
    ):
        result = await get_version_translation_contents_by_parent_ids(
            parent_segment_ids=["parent-seg-1"],
            version_text_id="version-text-1",
        )

    assert result == {}
