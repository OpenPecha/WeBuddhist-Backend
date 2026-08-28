from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, status

from pecha_api.texts.texts_openpecha_service import get_text_detail_by_id, trim_segment_content
from pecha_api.texts.text_openpecha_response_models import (
    TextDetailResponse,
    TextDetailWithContentResponse,
    CriticalEditionModel,
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

MOCK_EDITIONS = [
    CriticalEditionModel(id=EDITION_ID, type="critical")
]

MOCK_SEGMENTATIONS = [
    SegmentationResponseModel(id=SEGMENTATION_ID, edition_id=EDITION_ID, text_id=TEXT_ID)
]

MOCK_EDITION_CONTENT = EditionContentResponse(content="Hello World Foo Bar")

MOCK_SEGMENTS = SegmentationSegmentResponseModel(
    items=[
        SegmentSpans(id="span-1", lines=[SegmentLineModel(start=0, end=5)]),
        SegmentSpans(id="span-2", lines=[SegmentLineModel(start=6, end=11)]),
    ],
    has_more=False,
    offset=0,
    limit=30,
)


# ============================================================================
# get_text_detail_by_id
# ============================================================================

@pytest.mark.asyncio
async def test_get_text_detail_by_id_success(mocker):
    """Test happy path: assembles text detail with edition, segmentation, and segments"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_text_detail",
        new_callable=AsyncMock,
        return_value=MOCK_TEXT_DETAIL.model_copy(),
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_critical_editions",
        new_callable=AsyncMock,
        return_value=MOCK_EDITIONS,
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
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_segmentation_segments",
        new_callable=AsyncMock,
        return_value=MOCK_SEGMENTS,
    )

    result = await get_text_detail_by_id(text_id=TEXT_ID, offset=0, limit=30)

    assert isinstance(result, TextDetailWithContentResponse)
    assert result.text_detail.id == TEXT_ID
    assert result.text_detail.title == "Test Text"
    assert result.size == 2
    assert result.current_segment_position == 1
    assert len(result.content.sections) == 1
    assert len(result.content.sections[0].segments) == 2


@pytest.mark.asyncio
async def test_get_text_detail_by_id_passes_offset_and_limit_to_segments(mocker):
    """Test that offset and limit are forwarded to fetch_segmentation_segments"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_text_detail",
        new_callable=AsyncMock,
        return_value=MOCK_TEXT_DETAIL.model_copy(),
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_critical_editions",
        new_callable=AsyncMock,
        return_value=MOCK_EDITIONS,
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
        return_value=MOCK_SEGMENTS,
    )

    await get_text_detail_by_id(text_id=TEXT_ID, offset=10, limit=5)

    mock_fetch_segments.assert_called_once_with(
        segmentation_id=SEGMENTATION_ID, limit=5, offset=10
    )


@pytest.mark.asyncio
async def test_get_text_detail_by_id_uses_first_edition_for_segmentation(mocker):
    """Test that the first edition's id is used when fetching segmentation and content"""
    editions = [
        CriticalEditionModel(id="ed-first", type="critical"),
        CriticalEditionModel(id="ed-second", type="critical"),
    ]
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_text_detail",
        new_callable=AsyncMock,
        return_value=MOCK_TEXT_DETAIL.model_copy(),
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_critical_editions",
        new_callable=AsyncMock,
        return_value=editions,
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

    await get_text_detail_by_id(text_id=TEXT_ID, offset=0, limit=30)

    mock_fetch_segmentation.assert_called_once_with(edition_id="ed-first")
    mock_fetch_content.assert_called_once_with(edition_id="ed-first")


@pytest.mark.asyncio
async def test_get_text_detail_by_id_raises_404_when_no_editions(mocker):
    """Test 404 is raised when fetch_critical_editions returns an empty list"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_text_detail",
        new_callable=AsyncMock,
        return_value=MOCK_TEXT_DETAIL.model_copy(),
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_critical_editions",
        new_callable=AsyncMock,
        return_value=[],
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_text_detail_by_id(text_id=TEXT_ID, offset=0, limit=30)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert TEXT_ID in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_text_detail_by_id_propagates_fetch_text_detail_error(mocker):
    """Test that an HTTPException from fetch_text_detail is propagated"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_text_detail",
        new_callable=AsyncMock,
        side_effect=HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch text detail from upstream service",
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_text_detail_by_id(text_id=TEXT_ID, offset=0, limit=30)

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY


@pytest.mark.asyncio
async def test_get_text_detail_by_id_propagates_fetch_editions_error(mocker):
    """Test that an HTTPException from fetch_critical_editions is propagated"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_text_detail",
        new_callable=AsyncMock,
        return_value=MOCK_TEXT_DETAIL.model_copy(),
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_critical_editions",
        new_callable=AsyncMock,
        side_effect=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Text with id '{TEXT_ID}' not found",
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_text_detail_by_id(text_id=TEXT_ID, offset=0, limit=30)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


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


# =============================================================================
# get_titles_by_query_from_openpecha - Service Layer Tests
# =============================================================================

TITLE_SEARCH_PAYLOAD = {
    "items": [
        {
            "id": "RbdDgw67tA6XwdogCfqaK",
            "title": {"pi": "बुद्ध वन्दना"},
            "language": "pi",
            "license": "public",
        },
        {
            "id": "0V1UCd0qNSwwIJOEMcZYO",
            "title": {"en": "Buddha Vandana", "pi": "पञ्चसील याचना"},
            "language": "en",
            "license": "public",
        },
    ],
    "has_more": False,
    "offset": 0,
    "limit": 10,
}


@pytest.mark.asyncio
async def test_get_titles_by_query_from_openpecha_success(mocker):
    from pecha_api.texts.texts_openpecha_service import get_titles_by_query_from_openpecha

    mock_fetch = mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_texts_by_category",
        new=AsyncMock(return_value=TITLE_SEARCH_PAYLOAD),
    )

    result = await get_titles_by_query_from_openpecha(title="buddha", limit=10, offset=0)

    assert [item.id for item in result] == ["RbdDgw67tA6XwdogCfqaK", "0V1UCd0qNSwwIJOEMcZYO"]
    # Title is picked in the item's own language, not the first key.
    assert [item.title for item in result] == ["बुद्ध वन्दना", "Buddha Vandana"]
    mock_fetch.assert_awaited_once_with(title="buddha", limit=10, offset=0)


@pytest.mark.asyncio
async def test_get_titles_by_query_from_openpecha_no_matches(mocker):
    from pecha_api.texts.texts_openpecha_service import get_titles_by_query_from_openpecha

    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_texts_by_category",
        new=AsyncMock(return_value={"items": [], "has_more": False, "offset": 0, "limit": 10}),
    )

    result = await get_titles_by_query_from_openpecha(title="zzzznotathing", limit=10, offset=0)

    assert result == []


@pytest.mark.asyncio
async def test_get_titles_by_query_from_openpecha_skips_unusable_items(mocker):
    from pecha_api.texts.texts_openpecha_service import get_titles_by_query_from_openpecha

    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_texts_by_category",
        new=AsyncMock(
            return_value={
                "items": [
                    {"id": "", "title": {"en": "No id"}, "language": "en"},
                    {"id": "ok-1", "title": {}, "language": "en"},
                    "not-a-dict",
                    {"id": "ok-2", "title": {"en": "Keeps this"}, "language": "en"},
                ]
            }
        ),
    )

    result = await get_titles_by_query_from_openpecha(title="x", limit=10, offset=0)

    assert [item.id for item in result] == ["ok-2"]
    assert result[0].title == "Keeps this"


@pytest.mark.asyncio
async def test_get_titles_by_query_from_openpecha_upstream_error_raises_502(mocker):
    from pecha_api.texts.texts_openpecha_service import get_titles_by_query_from_openpecha

    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_texts_by_category",
        new=AsyncMock(side_effect=Exception("upstream down")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_titles_by_query_from_openpecha(title="buddha", limit=10, offset=0)

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY


@pytest.mark.asyncio
async def test_get_titles_by_query_from_openpecha_forwards_paging(mocker):
    from pecha_api.texts.texts_openpecha_service import get_titles_by_query_from_openpecha

    mock_fetch = mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_texts_by_category",
        new=AsyncMock(return_value={"items": []}),
    )

    await get_titles_by_query_from_openpecha(title="buddha", limit=50, offset=20)

    mock_fetch.assert_awaited_once_with(title="buddha", limit=50, offset=20)
