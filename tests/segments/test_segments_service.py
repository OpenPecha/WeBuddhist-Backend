import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

from pecha_api.texts.segments.segments_service import get_segments_details_by_ids
from pecha_api.texts.segments.segments_utils import SegmentUtils
from pecha_api.texts.segments.segments_response_models import SegmentDTO
from pecha_api.texts.segments.segments_enum import SegmentType
from pecha_api.error_contants import ErrorConstants


@pytest.mark.asyncio
async def test_validate_segment_exists_success():
    segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    with patch("pecha_api.texts.segments.segments_utils.check_segment_exists", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = True
        result = await SegmentUtils.validate_segment_exists(segment_id)
        assert result is True


@pytest.mark.asyncio
async def test_validate_segment_exists_not_found():
    segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    with patch("pecha_api.texts.segments.segments_utils.check_segment_exists", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = False
        with pytest.raises(HTTPException) as exc_info:
            await SegmentUtils.validate_segment_exists(segment_id)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE


@pytest.mark.asyncio
async def test_validate_segments_exists_success():
    segment_ids = ["efb26a06-f373-450b-ba57-e7a8d4dd5b64", "efb26a06-f373-450b-ba57-e7a8d4dd5b65"]
    with patch("pecha_api.texts.segments.segments_utils.check_all_segment_exists", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = True
        result = await SegmentUtils.validate_segments_exists(segment_ids)
        assert result is True


@pytest.mark.asyncio
async def test_validate_segments_exists_not_found():
    segment_ids = ["efb26a06-f373-450b-ba57-e7a8d4dd5b64", "efb26a06-f373-450b-ba57-e7a8d4dd5b65"]
    with patch("pecha_api.texts.segments.segments_utils.check_all_segment_exists", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = False
        with pytest.raises(HTTPException) as exc_info:
            await SegmentUtils.validate_segments_exists(segment_ids)
        assert exc_info.value.status_code == 404
        assert ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE in exc_info.value.detail
        assert str(segment_ids) in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_segments_details_by_ids_cache_hit():
    segment_ids = ["id_1", "id_2"]
    cached = {
        "id_1": SegmentDTO(
            id="id_1", text_id="t1", content="c1", mapping=[], type=SegmentType.SOURCE
        ),
        "id_2": SegmentDTO(
            id="id_2", text_id="t2", content="c2", mapping=[], type=SegmentType.SOURCE
        ),
    }

    with patch(
        "pecha_api.texts.segments.segments_service.get_segments_details_by_ids_cache",
        new_callable=AsyncMock,
        return_value=cached,
    ) as mock_cache, patch(
        "pecha_api.texts.segments.segments_service.get_segments_by_ids",
        new_callable=AsyncMock,
    ) as mock_repo:
        result = await get_segments_details_by_ids(segment_ids)
        assert result == cached
        mock_cache.assert_awaited_once()
        mock_repo.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_segments_details_by_ids_cache_miss_sets_cache():
    segment_ids = ["id_1", "id_2"]
    repo_result = {
        "id_1": SegmentDTO(
            id="id_1", text_id="t1", content="c1", mapping=[], type=SegmentType.SOURCE
        ),
        "id_2": SegmentDTO(
            id="id_2", text_id="t2", content="c2", mapping=[], type=SegmentType.SOURCE
        ),
    }

    with patch(
        "pecha_api.texts.segments.segments_service.get_segments_details_by_ids_cache",
        new_callable=AsyncMock,
        return_value=None,
    ), patch(
        "pecha_api.texts.segments.segments_service.get_segments_by_ids",
        new_callable=AsyncMock,
        return_value=repo_result,
    ) as mock_repo, patch(
        "pecha_api.texts.segments.segments_service.set_segments_details_by_ids_cache",
        new_callable=AsyncMock,
    ) as mock_set:
        result = await get_segments_details_by_ids(segment_ids)
        assert result == repo_result
        mock_repo.assert_awaited_once_with(segment_ids=segment_ids)
        assert mock_set.await_count == 1
        assert mock_set.await_args.kwargs["segment_ids"] == segment_ids
