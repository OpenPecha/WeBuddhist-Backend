import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
import uuid
import pytest
from pecha_api.texts.segments.segments_service import (
    create_new_segment,
    remove_segments_by_text_id,
    fetch_segments_by_text_id,
    get_segments_details_by_ids,
)
from pecha_api.texts.segments.segments_utils import SegmentUtils
from pecha_api.texts.segments.segments_response_models import (
    CreateSegmentRequest,
    SegmentResponse,
    CreateSegment,
    SegmentDTO,
    MappingResponse,
)

from pecha_api.texts.segments.segments_enum import SegmentType


from pecha_api.texts.texts_response_models import TextDTO

from pecha_api.error_contants import ErrorConstants

@pytest.mark.asyncio
async def test_create_new_segment():
    """
    Test case for the create_new_segment function from the segments_service file
    """
    create_segment_request = CreateSegmentRequest(
        text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
        segments=[
            CreateSegment(
                content="content", 
                mapping=[],
                type=SegmentType.SOURCE
            )
        ]
    )

    with patch('pecha_api.texts.segments.segments_service.validate_user_exists', return_value=True), \
        patch('pecha_api.texts.segments.segments_service.TextUtils.validate_text_exists', new_callable=AsyncMock, return_value=True), \
        patch('pecha_api.texts.segments.segments_service.create_segment', new_callable=AsyncMock) as mock_create_segment:
        mock_segment = type('Segment', (), {
            'id': uuid.UUID("efb26a06-f373-450b-ba57-e7a8d4dd5b64"),
            'pecha_segment_id': "pecha_efb26a06-f373-450b-ba57-e7a8d4dd5b64",
            'text_id': "efb26a06-f373-450b-ba57-e7a8d4dd5b64",
            'content': "content",
            'mapping': [],
            'type': SegmentType.SOURCE,
            'model_dump': lambda self: {
                'id': self.id,
                'pecha_segment_id': self.pecha_segment_id,
                'text_id': self.text_id,
                'content': self.content,
                'mapping': self.mapping,
                'type': self.type
            }
        })()
        mock_create_segment.return_value = [mock_segment]
        
        response = await create_new_segment(
            create_segment_request=create_segment_request,
            token="admin"
        )
        
        expected_response = SegmentResponse(
            segments=[
                SegmentDTO(
                    id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
                    pecha_segment_id="pecha_efb26a06-f373-450b-ba57-e7a8d4dd5b64",
                    text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
                    content="content",
                    mapping=[],
                    type=SegmentType.SOURCE
                )
            ]
        )
        assert response == expected_response


@pytest.mark.asyncio
async def test_create_new_segment_invalid_user():
    """
    Test case for the create_new_segment function fails due to admin
    """
    create_segment_request = CreateSegmentRequest(
        text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
        segments=[
            CreateSegment(
                content="content", 
                mapping=[],
                type=SegmentType.SOURCE
            )
        ]
    )

    with patch('pecha_api.texts.segments.segments_service.validate_user_exists', return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await create_new_segment(
                create_segment_request=create_segment_request,
                token="no_admin"
            )
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == ErrorConstants.TOKEN_ERROR_MESSAGE

@pytest.mark.asyncio
async def test_validate_segment_exists_success():
    segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    with patch('pecha_api.texts.segments.segments_utils.check_segment_exists', new_callable=AsyncMock) as mock_check:
        mock_check.return_value = True
        result = await SegmentUtils.validate_segment_exists(segment_id)
        assert result is True

@pytest.mark.asyncio
async def test_validate_segment_exists_not_found():
    segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    with patch('pecha_api.texts.segments.segments_utils.check_segment_exists', new_callable=AsyncMock) as mock_check:
        mock_check.return_value = False
        with pytest.raises(HTTPException) as exc_info:
            await SegmentUtils.validate_segment_exists(segment_id)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE

@pytest.mark.asyncio
async def test_validate_segments_exists_success():
    segment_ids = ["efb26a06-f373-450b-ba57-e7a8d4dd5b64", "efb26a06-f373-450b-ba57-e7a8d4dd5b65"]
    with patch('pecha_api.texts.segments.segments_utils.check_all_segment_exists', new_callable=AsyncMock) as mock_check:
        mock_check.return_value = True
        result = await SegmentUtils.validate_segments_exists(segment_ids)
        assert result is True

@pytest.mark.asyncio
async def test_validate_segments_exists_not_found():
    segment_ids = ["efb26a06-f373-450b-ba57-e7a8d4dd5b64", "efb26a06-f373-450b-ba57-e7a8d4dd5b65"]
    with patch('pecha_api.texts.segments.segments_utils.check_all_segment_exists', new_callable=AsyncMock) as mock_check:
        mock_check.return_value = False
        with pytest.raises(HTTPException) as exc_info:
            await SegmentUtils.validate_segments_exists(segment_ids)
        assert exc_info.value.status_code == 404
        # The error message includes the segment IDs in the format: "Segment not found {segment_ids}"
        assert ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE in exc_info.value.detail
        assert str(segment_ids) in exc_info.value.detail


@pytest.mark.asyncio
async def test_remove_segments_by_text_id_success():
    text_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    with patch("pecha_api.texts.segments.segments_service.delete_segments_by_text_id", new_callable=AsyncMock, return_value=True),\
        patch("pecha_api.texts.segments.segments_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=True):
        
        response = await remove_segments_by_text_id(text_id=text_id)
        
        assert response is not None
    
@pytest.mark.asyncio
async def test_remove_segments_by_text_id_invalid_text_id():
    text_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    with patch("pecha_api.texts.segments.segments_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await remove_segments_by_text_id(text_id=text_id)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.TEXT_NOT_FOUND_MESSAGE

@pytest.mark.asyncio
async def test_fetch_segments_by_text_id_success():
    text_id = "text_id"
    mock_segments = [
        SegmentDTO(
            id=f"id_{i}",
            text_id=f"{text_id}_{i}",
            content=f"content_{i}",
            mapping=[],
            type=SegmentType.SOURCE
        )
        for i in range(1,6)
    ]
    with patch("pecha_api.texts.segments.segments_service.get_segments_by_text_id", new_callable=AsyncMock, return_value=mock_segments):
        response = await fetch_segments_by_text_id(text_id=text_id)

        assert response is not None
        assert len(response) == 5
        assert response[0].id == "id_1"
        assert response[0].text_id == f"{text_id}_1"
        assert response[0].type == SegmentType.SOURCE


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
    ) as mock_cache, patch(
        "pecha_api.texts.segments.segments_service.get_segments_by_ids",
        new_callable=AsyncMock,
        return_value=repo_result,
    ) as mock_repo, patch(
        "pecha_api.texts.segments.segments_service.set_segments_details_by_ids_cache",
        new_callable=AsyncMock,
    ) as mock_set:
        result = await get_segments_details_by_ids(segment_ids)
        assert result == repo_result
        mock_cache.assert_awaited_once()
        mock_repo.assert_awaited_once_with(segment_ids=segment_ids)
        # ensure cache set called with expected segment_ids
        assert mock_set.await_count == 1
        called_kwargs = mock_set.await_args.kwargs
        assert called_kwargs["segment_ids"] == segment_ids
