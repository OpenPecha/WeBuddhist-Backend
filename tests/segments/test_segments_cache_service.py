import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from pecha_api.texts.segments.segments_cache_service import (
    get_segment_details_by_id_cache,
    set_segment_details_by_id_cache,
)

from pecha_api.texts.segments.segments_response_models import (
    SegmentDTO,
)
from pecha_api.texts.segments.segments_enum import SegmentType

@pytest.mark.asyncio
async def test_get_segment_details_by_id_cache_success():
    mock_segment = SegmentDTO(
        id="segment_id",
        text_id="text_id",
        mapping=[],
        content="content",
        type=SegmentType.CONTENT
    )

    with patch("pecha_api.texts.segments.segments_cache_service.get_cache_data", new_callable=AsyncMock, return_value=mock_segment):
        response = await get_segment_details_by_id_cache(segment_id="segment_id", text_details=True)

        assert response is not None
        assert isinstance(response, SegmentDTO)
        assert response.id == "segment_id"

@pytest.mark.asyncio
async def test_set_segment_details_by_id_cache_success():

    mock_segment=SegmentDTO(
        id="segment_id",
        text_id="text_id",
        mapping=[],
        content="content",
        type=SegmentType.CONTENT
    )

    with patch("pecha_api.texts.segments.segments_cache_service.set_cache", new_callable=AsyncMock, return_value=None):
        response = await set_segment_details_by_id_cache(segment_id="segment_id", text_details=True, data=mock_segment)
