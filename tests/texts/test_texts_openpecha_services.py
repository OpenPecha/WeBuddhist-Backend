from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, status

from pecha_api.texts.texts_enums import PaginationDirection
from pecha_api.texts.texts_openpecha_service import get_text_detail_by_id, trim_segment_content
from pecha_api.texts.text_openpecha_response_models import (
    TextDetailResponse,
    TextDetailWithContentResponse,
    TextDetailsRequest,
    ContributionModel,
    SegmentationResponseModel,
    SegmentationSegmentResponseModel,
    EditionContentResponse,
    SegmentContentResponse,
    SegmentSpans,
    SegmentLineModel,
)

TEXT_ID = "OP0001"
EDITION_ID = "ed-1"
SEGMENTATION_ID = "seg-1"

MOCK_TEXT_DETAIL = TextDetailResponse(
    id=TEXT_ID,
    title={"en": "Test Text"},
    language="en",
    category_id="cat-1",
    license="CC0",
    contributions=[ContributionModel(role="author", person_name={"en": "Author Name"})],
    commentaries=[],
    translations=[],
)

MOCK_SEGMENTATIONS = [
    SegmentationResponseModel(id=SEGMENTATION_ID, edition_id=EDITION_ID, text_id=TEXT_ID)
]

MOCK_EDITION_CONTENT = EditionContentResponse(content="Hello World Foo Bar")

MOCK_SEGMENTS = SegmentationSegmentResponseModel(
    items=[
        SegmentSpans(id="span-1", lines=[SegmentLineModel(start=0, end=5)]),
        SegmentSpans(id="span-2", lines=[SegmentLineModel(start=6, end=11)]),
        SegmentSpans(id="span-3", lines=[SegmentLineModel(start=12, end=15)]),
        SegmentSpans(id="span-4", lines=[SegmentLineModel(start=16, end=19)]),
    ],
    has_more=False,
    offset=0,
    limit=500,
)


def _segments(result: TextDetailWithContentResponse):
    return result.content.sections[0].segments


def _patch_common(mocker, segmentations=None, segments_page=MOCK_SEGMENTS):
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_text_id",
        new_callable=AsyncMock,
        return_value=TEXT_ID,
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_text_detail",
        new_callable=AsyncMock,
        return_value=MOCK_TEXT_DETAIL.model_copy(),
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_editions_segmentation",
        new_callable=AsyncMock,
        return_value=segmentations if segmentations is not None else MOCK_SEGMENTATIONS,
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_content",
        new_callable=AsyncMock,
        return_value=MOCK_EDITION_CONTENT,
    )
    return mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_segmentation_segments",
        new_callable=AsyncMock,
        return_value=segments_page,
    )


# ============================================================================
# get_text_detail_by_id
# ============================================================================

@pytest.mark.asyncio
async def test_get_text_detail_by_id_defaults_to_first_segment(mocker):
    """With no segment_id, pagination anchors at the first segment"""
    _patch_common(mocker)

    result = await get_text_detail_by_id(
        edition_id=EDITION_ID,
        text_details_request=TextDetailsRequest(size=2),
    )

    assert isinstance(result, TextDetailWithContentResponse)
    assert result.text_detail.id == TEXT_ID
    assert result.text_detail.title == "Test Text"
    assert result.total_segments == 4
    assert result.current_segment_position == 1
    assert [s.segment_id for s in _segments(result)] == ["span-1", "span-2"]
    assert _segments(result)[0].content == "Hello"
    assert result.has_more_up is False
    assert result.has_more_down is True


@pytest.mark.asyncio
async def test_get_text_detail_by_id_next_direction_from_segment_id(mocker):
    """direction=NEXT pages forward from the given segment_id"""
    _patch_common(mocker)

    result = await get_text_detail_by_id(
        edition_id=EDITION_ID,
        text_details_request=TextDetailsRequest(segment_id="span-2", size=2, direction=PaginationDirection.NEXT),
    )

    assert result.current_segment_position == 2
    assert [s.segment_id for s in _segments(result)] == ["span-2", "span-3"]
    assert [s.segment_number for s in _segments(result)] == [2, 3]
    assert result.has_more_up is True
    assert result.has_more_down is True


@pytest.mark.asyncio
async def test_get_text_detail_by_id_previous_direction_from_segment_id(mocker):
    """direction=PREVIOUS pages backward from the given segment_id"""
    _patch_common(mocker)

    result = await get_text_detail_by_id(
        edition_id=EDITION_ID,
        text_details_request=TextDetailsRequest(segment_id="span-3", size=2, direction=PaginationDirection.PREVIOUS),
    )

    assert result.current_segment_position == 3
    assert [s.segment_id for s in _segments(result)] == ["span-2", "span-3"]
    assert result.has_more_up is True
    assert result.has_more_down is True


@pytest.mark.asyncio
async def test_get_text_detail_by_id_no_more_down_at_end(mocker):
    """has_more_down is False once the window reaches the last segment"""
    _patch_common(mocker)

    result = await get_text_detail_by_id(
        edition_id=EDITION_ID,
        text_details_request=TextDetailsRequest(segment_id="span-4", size=2, direction=PaginationDirection.NEXT),
    )

    assert [s.segment_id for s in _segments(result)] == ["span-4"]
    assert result.has_more_down is False


@pytest.mark.asyncio
async def test_get_text_detail_by_id_uses_start_and_end_when_provided(mocker):
    """start/end select an explicit segment_number window, independent of size"""
    _patch_common(mocker)

    result = await get_text_detail_by_id(
        edition_id=EDITION_ID,
        text_details_request=TextDetailsRequest(start=2, end=3, size=20),
    )

    assert [s.segment_id for s in _segments(result)] == ["span-2", "span-3"]
    assert [s.segment_number for s in _segments(result)] == [2, 3]
    assert result.current_segment_position == 2
    assert result.has_more_up is True
    assert result.has_more_down is True


@pytest.mark.asyncio
async def test_get_text_detail_by_id_start_end_takes_priority_over_segment_id(mocker):
    """When both are given, start/end wins over segment_id/direction"""
    _patch_common(mocker)

    result = await get_text_detail_by_id(
        edition_id=EDITION_ID,
        text_details_request=TextDetailsRequest(
            segment_id="span-4", direction=PaginationDirection.PREVIOUS, start=1, end=2,
        ),
    )

    assert [s.segment_id for s in _segments(result)] == ["span-1", "span-2"]
    assert result.has_more_up is False


@pytest.mark.asyncio
async def test_get_text_detail_by_id_start_end_clamped_to_total_segments(mocker):
    """An end beyond total_segments is clamped and has_more_down is False"""
    _patch_common(mocker)

    result = await get_text_detail_by_id(
        edition_id=EDITION_ID,
        text_details_request=TextDetailsRequest(start=3, end=10),
    )

    assert [s.segment_id for s in _segments(result)] == ["span-3", "span-4"]
    assert result.has_more_down is False


@pytest.mark.asyncio
async def test_get_text_detail_by_id_fetches_all_pages_of_segments(mocker):
    """The full segment list is materialized across multiple upstream pages before windowing"""
    page_1 = SegmentationSegmentResponseModel(
        items=[SegmentSpans(id="span-1", lines=[SegmentLineModel(start=0, end=5)])],
        has_more=True,
        offset=0,
        limit=1,
    )
    page_2 = SegmentationSegmentResponseModel(
        items=[SegmentSpans(id="span-2", lines=[SegmentLineModel(start=6, end=11)])],
        has_more=False,
        offset=1,
        limit=1,
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_text_id",
        new_callable=AsyncMock,
        return_value=TEXT_ID,
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_text_detail",
        new_callable=AsyncMock,
        return_value=MOCK_TEXT_DETAIL.model_copy(),
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_editions_segmentation",
        new_callable=AsyncMock,
        return_value=MOCK_SEGMENTATIONS,
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_content",
        new_callable=AsyncMock,
        return_value=MOCK_EDITION_CONTENT,
    )
    mock_fetch_segments = mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_segmentation_segments",
        new_callable=AsyncMock,
        side_effect=[page_1, page_2],
    )

    result = await get_text_detail_by_id(
        edition_id=EDITION_ID,
        text_details_request=TextDetailsRequest(size=10),
    )

    assert result.total_segments == 2
    assert mock_fetch_segments.call_count == 2


@pytest.mark.asyncio
async def test_get_text_detail_by_id_passes_edition_id_to_segmentation_and_content(mocker):
    """Test that the given edition_id is used directly for segmentation and content, with no edition lookup by text_id"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_text_id",
        new_callable=AsyncMock,
        return_value=TEXT_ID,
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_text_detail",
        new_callable=AsyncMock,
        return_value=MOCK_TEXT_DETAIL.model_copy(),
    )
    mock_fetch_segmentation = mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_editions_segmentation",
        new_callable=AsyncMock,
        return_value=MOCK_SEGMENTATIONS,
    )
    mock_fetch_content = mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_content",
        new_callable=AsyncMock,
        return_value=MOCK_EDITION_CONTENT,
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_segmentation_segments",
        new_callable=AsyncMock,
        return_value=MOCK_SEGMENTS,
    )

    await get_text_detail_by_id(edition_id=EDITION_ID, text_details_request=TextDetailsRequest())

    mock_fetch_segmentation.assert_called_once_with(edition_id=EDITION_ID)
    mock_fetch_content.assert_called_once_with(edition_id=EDITION_ID)


@pytest.mark.asyncio
async def test_get_text_detail_by_id_raises_404_when_no_segmentation(mocker):
    """Test 404 is raised when fetch_editions_segmentation returns an empty list"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_text_id",
        new_callable=AsyncMock,
        return_value=TEXT_ID,
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_text_detail",
        new_callable=AsyncMock,
        return_value=MOCK_TEXT_DETAIL.model_copy(),
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_editions_segmentation",
        new_callable=AsyncMock,
        return_value=[],
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_text_detail_by_id(edition_id=EDITION_ID, text_details_request=TextDetailsRequest())

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert EDITION_ID in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_text_detail_by_id_raises_404_when_segment_id_not_found(mocker):
    """Test 404 is raised when the requested segment_id doesn't exist in the segmentation"""
    _patch_common(mocker)

    with pytest.raises(HTTPException) as exc_info:
        await get_text_detail_by_id(
            edition_id=EDITION_ID,
            text_details_request=TextDetailsRequest(segment_id="missing-segment"),
        )

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_text_detail_by_id_propagates_fetch_edition_text_id_error(mocker):
    """Test that an HTTPException from fetch_edition_text_id is propagated"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_text_id",
        new_callable=AsyncMock,
        side_effect=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Edition with id '{EDITION_ID}' not found",
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_text_detail_by_id(edition_id=EDITION_ID, text_details_request=TextDetailsRequest())

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_text_detail_by_id_propagates_fetch_text_detail_error(mocker):
    """Test that an HTTPException from fetch_text_detail is propagated"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_text_id",
        new_callable=AsyncMock,
        return_value=TEXT_ID,
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_text_detail",
        new_callable=AsyncMock,
        side_effect=HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch text detail from upstream service",
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_text_detail_by_id(edition_id=EDITION_ID, text_details_request=TextDetailsRequest())

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY


@pytest.mark.asyncio
async def test_get_text_detail_by_id_propagates_fetch_editions_segmentation_error(mocker):
    """Test that an HTTPException from fetch_editions_segmentation is propagated"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_text_id",
        new_callable=AsyncMock,
        return_value=TEXT_ID,
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_text_detail",
        new_callable=AsyncMock,
        return_value=MOCK_TEXT_DETAIL.model_copy(),
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_editions_segmentation",
        new_callable=AsyncMock,
        side_effect=HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch editions segmentation from upstream service",
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_text_detail_by_id(edition_id=EDITION_ID, text_details_request=TextDetailsRequest())

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY


@pytest.mark.asyncio
async def test_get_text_detail_by_id_applies_translation_when_version_id_provided(mocker):
    """When version_id is given, each segment's translation is resolved from the related segment in that edition"""
    version_id = "ed-translation"
    translation_content = "Bonjour Monde"

    async def _content_side_effect(edition_id):
        if edition_id == version_id:
            return EditionContentResponse(content=translation_content)
        return MOCK_EDITION_CONTENT

    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_text_id",
        new_callable=AsyncMock,
        return_value=TEXT_ID,
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_text_detail",
        new_callable=AsyncMock,
        return_value=MOCK_TEXT_DETAIL.model_copy(),
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_editions_segmentation",
        new_callable=AsyncMock,
        return_value=MOCK_SEGMENTATIONS,
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_content",
        side_effect=_content_side_effect,
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_segmentation_segments",
        new_callable=AsyncMock,
        return_value=MOCK_SEGMENTS,
    )
    mock_related = mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_related_segments",
        new_callable=AsyncMock,
        return_value=[{"id": "trans-span-1", "text_id": version_id, "lines": [{"start": 0, "end": 7}]}],
    )

    result = await get_text_detail_by_id(
        edition_id=EDITION_ID,
        text_details_request=TextDetailsRequest(size=2, version_id=version_id),
    )

    segments = _segments(result)
    assert segments[0].translation == "Bonjour"
    mock_related.assert_any_call(segment_id="span-1", text_id=version_id)


@pytest.mark.asyncio
async def test_get_text_detail_by_id_translation_none_when_no_related_segment(mocker):
    """A segment with no related segment in the translation edition keeps translation=None"""
    _patch_common(mocker)
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_related_segments",
        new_callable=AsyncMock,
        return_value=[],
    )

    result = await get_text_detail_by_id(
        edition_id=EDITION_ID,
        text_details_request=TextDetailsRequest(size=2, version_id="ed-translation"),
    )

    assert all(s.translation is None for s in _segments(result))


@pytest.mark.asyncio
async def test_get_text_detail_by_id_no_translation_lookup_without_version_id(mocker):
    """Without version_id, related segments are never fetched and translation stays None"""
    _patch_common(mocker)
    mock_related = mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_related_segments",
        new_callable=AsyncMock,
    )

    result = await get_text_detail_by_id(
        edition_id=EDITION_ID,
        text_details_request=TextDetailsRequest(size=2),
    )

    mock_related.assert_not_called()
    assert all(s.translation is None for s in _segments(result))


# ============================================================================
# trim_segment_content
# ============================================================================

def test_trim_segment_content_extracts_correct_slices():
    """Test that content is sliced correctly according to segment line spans"""
    content = "Hello World"
    segments = SegmentationSegmentResponseModel(
        items=[
            SegmentSpans(id="s1", lines=[SegmentLineModel(start=0, end=5)]),
            SegmentSpans(id="s2", lines=[SegmentLineModel(start=6, end=11)]),
        ],
        has_more=False,
        offset=0,
        limit=30,
    )

    result = trim_segment_content(edition_content=content, segments=segments)

    assert len(result.contents) == 2
    assert result.contents[0].id == "s1"
    assert result.contents[0].content == "Hello"
    assert result.contents[0].segment_number == 1
    assert result.contents[1].id == "s2"
    assert result.contents[1].content == "World"
    assert result.contents[1].segment_number == 2


def test_trim_segment_content_multiple_lines_per_segment():
    """Test that a segment spanning multiple lines concatenates all slices"""
    content = "abcdefghij"
    segments = SegmentationSegmentResponseModel(
        items=[
            SegmentSpans(
                id="s1",
                lines=[
                    SegmentLineModel(start=0, end=3),
                    SegmentLineModel(start=5, end=8),
                ],
            )
        ],
        has_more=False,
        offset=0,
        limit=30,
    )

    result = trim_segment_content(edition_content=content, segments=segments)

    assert len(result.contents) == 1
    assert result.contents[0].content == "abcfgh"


def test_trim_segment_content_empty_segments():
    """Test that empty segment list returns empty contents"""
    segments = SegmentationSegmentResponseModel(
        items=[],
        has_more=False,
        offset=0,
        limit=30,
    )

    result = trim_segment_content(edition_content="some content", segments=segments)

    assert result.contents == []
    assert result.has_more is False


def test_trim_segment_content_preserves_pagination_metadata():
    """Test that has_more, offset, and limit are passed through unchanged"""
    segments = SegmentationSegmentResponseModel(
        items=[SegmentSpans(id="s1", lines=[SegmentLineModel(start=0, end=3)])],
        has_more=True,
        offset=10,
        limit=5,
    )

    result = trim_segment_content(edition_content="abcdef", segments=segments)

    assert result.has_more is True
    assert result.offset == 10
    assert result.limit == 5


def test_trim_segment_content_segment_numbers_are_sequential():
    """Test that segment_number increments from 1 for each item"""
    content = "aabbcc"
    segments = SegmentationSegmentResponseModel(
        items=[
            SegmentSpans(id="s1", lines=[SegmentLineModel(start=0, end=2)]),
            SegmentSpans(id="s2", lines=[SegmentLineModel(start=2, end=4)]),
            SegmentSpans(id="s3", lines=[SegmentLineModel(start=4, end=6)]),
        ],
        has_more=False,
        offset=0,
        limit=30,
    )

    result = trim_segment_content(edition_content=content, segments=segments)

    assert [s.segment_number for s in result.contents] == [1, 2, 3]
