from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, status

from pecha_api.texts.texts_enums import PaginationDirection
from pecha_api.texts.texts_openpecha_service import get_text_detail_by_id, trim_segment_content
from pecha_api.texts.text_openpecha_response_models import (
    CriticalEditionModel,
    TextDetailResponse,
    TextDetailWithContentResponse,
    TextDetailsRequest,
    ContributionModel,
    EditionAlignmentPairModel,
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


# ============================================================================
# get_text_detail_by_id -- accepting a text id instead of an edition id
# ============================================================================

@pytest.mark.asyncio
async def test_get_text_detail_by_id_resolves_text_id_to_critical_edition(mocker):
    """Callers across the app (search results, text/version listings, related
    segments) only have a text id, not an edition id. When fetch_edition_text_id
    404s on the given id, it should be treated as a text id and resolved to its
    first critical edition before continuing."""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_text_id",
        new_callable=AsyncMock,
        side_effect=HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found"),
    )
    mock_fetch_critical_editions = mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_critical_editions",
        new_callable=AsyncMock,
        return_value=[CriticalEditionModel(id=EDITION_ID, type="critical")],
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

    result = await get_text_detail_by_id(edition_id=TEXT_ID, text_details_request=TextDetailsRequest())

    mock_fetch_critical_editions.assert_called_once_with(text_id=TEXT_ID)
    mock_fetch_segmentation.assert_called_once_with(edition_id=EDITION_ID)
    mock_fetch_content.assert_called_once_with(edition_id=EDITION_ID)
    assert result.content.text_id == TEXT_ID
    assert result.content.id == EDITION_ID


@pytest.mark.asyncio
async def test_get_text_detail_by_id_raises_404_when_text_has_no_critical_edition(mocker):
    """If the id isn't an edition and the text has no critical edition either,
    surface a 404 instead of an unrelated failure further down the pipeline."""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_text_id",
        new_callable=AsyncMock,
        side_effect=HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found"),
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_critical_editions",
        new_callable=AsyncMock,
        return_value=[],
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_text_detail_by_id(edition_id=TEXT_ID, text_details_request=TextDetailsRequest())

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert TEXT_ID in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_text_detail_by_id_raises_502_when_critical_edition_fetch_fails(mocker):
    """A dependency failure while fetching critical editions must not be
    reported as the text simply not having one — that would mask an outage
    as a permanent 404."""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_text_id",
        new_callable=AsyncMock,
        side_effect=HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found"),
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_critical_editions",
        new_callable=AsyncMock,
        side_effect=Exception("upstream failure"),
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_text_detail_by_id(edition_id=TEXT_ID, text_details_request=TextDetailsRequest())

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY


@pytest.mark.asyncio
async def test_get_text_detail_by_id_reraises_404_when_id_is_neither_edition_nor_text(mocker):
    """An id that is neither a valid edition nor a valid text is a genuine
    client error, not a dependency failure — fetch_critical_editions itself
    raises a 404 HTTPException for this case, which must propagate as-is
    rather than being swallowed into a misleading 502."""
    bogus_id = "does-not-exist"
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_text_id",
        new_callable=AsyncMock,
        side_effect=HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found"),
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_critical_editions",
        new_callable=AsyncMock,
        side_effect=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Text with id '{bogus_id}' not found",
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_text_detail_by_id(edition_id=bogus_id, text_details_request=TextDetailsRequest())

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_text_detail_by_id_resolves_version_id_text_id_to_critical_edition(mocker):
    """The translations/versions listings hand out text ids, so a version_id
    picked from them must resolve to an edition before alignment lookup, which
    only works between edition ids."""
    version_text_id = "OP0002"
    version_edition_id = "ed-2"

    async def fetch_edition_text_id(edition_id: str):
        if edition_id == EDITION_ID:
            return TEXT_ID
        if edition_id == version_edition_id:
            return version_text_id
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")

    _patch_common(mocker)
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_text_id",
        new_callable=AsyncMock,
        side_effect=fetch_edition_text_id,
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_critical_editions",
        new_callable=AsyncMock,
        return_value=[CriticalEditionModel(id=version_edition_id, type="critical")],
    )
    mock_alignment_pairs = mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_alignment_pairs",
        new_callable=AsyncMock,
        return_value=([EditionAlignmentPairModel(source_segment_id="span-1", target_segment_id="t-1")], False),
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_segment_content",
        new_callable=AsyncMock,
        return_value="translated content",
    )

    result = await get_text_detail_by_id(
        edition_id=EDITION_ID,
        text_details_request=TextDetailsRequest(version_id=version_text_id),
    )

    mock_alignment_pairs.assert_any_call(
        source_edition_id=EDITION_ID,
        target_edition_id=version_edition_id,
        limit=mocker.ANY,
        offset=0,
    )
    translation = _segments(result)[0].translation
    assert translation.content == "translated content"
    assert translation.text_id == version_edition_id


@pytest.mark.asyncio
async def test_get_text_detail_by_id_reraises_non_404_edition_lookup_errors(mocker):
    """A non-404 failure while checking the id should propagate as-is rather
    than being swallowed into the text-id fallback path."""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_text_id",
        new_callable=AsyncMock,
        side_effect=HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="upstream error"),
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_text_detail_by_id(edition_id=EDITION_ID, text_details_request=TextDetailsRequest())

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY


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
async def test_get_text_detail_by_id_falls_back_to_404_when_edition_lookup_404s_and_no_critical_edition(mocker):
    """A 404 from fetch_edition_text_id means the given id isn't an edition, so it
    falls back to treating it as a text id. If that text also has no critical
    edition, the final result is still a 404 — but critical-edition lookup must
    be mocked here, or this silently depends on a live upstream call."""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_text_id",
        new_callable=AsyncMock,
        side_effect=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Edition with id '{EDITION_ID}' not found",
        ),
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_critical_editions",
        new_callable=AsyncMock,
        return_value=[],
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
async def test_get_text_detail_by_id_applies_translation_direct_alignment(mocker):
    """A direct edition_id -> version_id alignment is used as-is, resolving translation
    content per segment via fetch_segment_content."""
    version_id = "ed-translation"
    translation_by_id = {"trans-span-1": "Bonjour", "trans-span-2": "Monde"}

    async def _pairs_side_effect(source_edition_id, target_edition_id, limit=500, offset=0):
        if source_edition_id == EDITION_ID and target_edition_id == version_id:
            return (
                [
                    EditionAlignmentPairModel(source_segment_id="span-1", target_segment_id="trans-span-1"),
                    EditionAlignmentPairModel(source_segment_id="span-2", target_segment_id="trans-span-2"),
                ],
                False,
            )
        return [], False

    async def _content_side_effect(segment_id):
        return translation_by_id.get(segment_id)

    _patch_common(mocker)
    mock_pairs = mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_alignment_pairs",
        side_effect=_pairs_side_effect,
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_segment_content",
        side_effect=_content_side_effect,
    )

    result = await get_text_detail_by_id(
        edition_id=EDITION_ID,
        text_details_request=TextDetailsRequest(size=2, version_id=version_id),
    )

    segments = _segments(result)
    assert segments[0].translation.content == "Bonjour"
    assert segments[0].translation.text_id == version_id
    assert segments[0].translation.language == "en"
    assert segments[1].translation.content == "Monde"
    mock_pairs.assert_any_call(source_edition_id=EDITION_ID, target_edition_id=version_id, limit=500, offset=0)


@pytest.mark.asyncio
async def test_get_text_detail_by_id_applies_translation_reverse_alignment(mocker):
    """When there's no direct edition_id -> version_id alignment but one exists the other way
    round (version_id -> edition_id), it's used and inverted."""
    version_id = "ed-translation"
    translation_by_id = {"trans-span-1": "Bonjour", "trans-span-2": "Monde"}

    async def _pairs_side_effect(source_edition_id, target_edition_id, limit=500, offset=0):
        if source_edition_id == version_id and target_edition_id == EDITION_ID:
            return (
                [
                    EditionAlignmentPairModel(source_segment_id="trans-span-1", target_segment_id="span-1"),
                    EditionAlignmentPairModel(source_segment_id="trans-span-2", target_segment_id="span-2"),
                ],
                False,
            )
        return [], False

    async def _content_side_effect(segment_id):
        return translation_by_id.get(segment_id)

    _patch_common(mocker)
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_alignment_pairs",
        side_effect=_pairs_side_effect,
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_segment_content",
        side_effect=_content_side_effect,
    )

    result = await get_text_detail_by_id(
        edition_id=EDITION_ID,
        text_details_request=TextDetailsRequest(size=2, version_id=version_id),
    )

    segments = _segments(result)
    assert segments[0].translation.content == "Bonjour"
    assert segments[1].translation.content == "Monde"


@pytest.mark.asyncio
async def test_get_text_detail_by_id_applies_translation_via_shared_root_pivot(mocker):
    """Two translations of the same root text are typically only aligned to that shared root
    edition, not to each other directly - translation resolution should compose the mapping
    edition_id -> root -> version_id through that pivot edition."""
    version_id = "ed-translation"
    version_text_id = "version-text-id"
    root_text_id = "root-text-id"
    pivot_edition_id = "pivot-edition-id"
    translation_by_id = {"trans-span-1": "Bonjour", "trans-span-2": "Monde"}

    edition_text_detail = MOCK_TEXT_DETAIL.model_copy(update={"translation_of": root_text_id})
    version_text_detail = MOCK_TEXT_DETAIL.model_copy(update={"id": version_text_id, "translation_of": root_text_id})

    async def _text_id_side_effect(edition_id):
        return {EDITION_ID: TEXT_ID, version_id: version_text_id}[edition_id]

    async def _text_detail_side_effect(text_id):
        return {TEXT_ID: edition_text_detail, version_text_id: version_text_detail}[text_id]

    async def _pairs_side_effect(source_edition_id, target_edition_id, limit=500, offset=0):
        if source_edition_id == EDITION_ID and target_edition_id == pivot_edition_id:
            return (
                [
                    EditionAlignmentPairModel(source_segment_id="span-1", target_segment_id="root-span-1"),
                    EditionAlignmentPairModel(source_segment_id="span-2", target_segment_id="root-span-2"),
                ],
                False,
            )
        if source_edition_id == version_id and target_edition_id == pivot_edition_id:
            return (
                [
                    EditionAlignmentPairModel(source_segment_id="trans-span-1", target_segment_id="root-span-1"),
                    EditionAlignmentPairModel(source_segment_id="trans-span-2", target_segment_id="root-span-2"),
                ],
                False,
            )
        return [], False

    async def _content_side_effect(segment_id):
        return translation_by_id.get(segment_id)

    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_text_id",
        side_effect=_text_id_side_effect,
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_text_detail",
        side_effect=_text_detail_side_effect,
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
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_alignment_pairs",
        side_effect=_pairs_side_effect,
    )
    mock_critical_editions = mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_critical_editions",
        new_callable=AsyncMock,
        return_value=[CriticalEditionModel(id=pivot_edition_id, type="critical")],
    )
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_segment_content",
        side_effect=_content_side_effect,
    )

    result = await get_text_detail_by_id(
        edition_id=EDITION_ID,
        text_details_request=TextDetailsRequest(size=2, version_id=version_id),
    )

    segments = _segments(result)
    assert segments[0].translation.content == "Bonjour"
    assert segments[0].translation.text_id == version_id
    assert segments[0].translation.language == "en"
    assert segments[1].translation.content == "Monde"
    mock_critical_editions.assert_called_once_with(text_id=root_text_id)


@pytest.mark.asyncio
async def test_get_text_detail_by_id_translation_none_when_no_alignment_found(mocker):
    """No alignment (direct, reverse, or via a shared root) leaves translation=None on every segment"""
    _patch_common(mocker)
    mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_alignment_pairs",
        new_callable=AsyncMock,
        return_value=([], False),
    )

    result = await get_text_detail_by_id(
        edition_id=EDITION_ID,
        text_details_request=TextDetailsRequest(size=2, version_id="ed-translation"),
    )

    assert all(s.translation is None for s in _segments(result))


@pytest.mark.asyncio
async def test_get_text_detail_by_id_no_translation_lookup_without_version_id(mocker):
    """Without version_id, alignment pairs are never fetched and translation stays None"""
    _patch_common(mocker)
    mock_pairs = mocker.patch(
        "pecha_api.texts.texts_openpecha_service.fetch_edition_alignment_pairs",
        new_callable=AsyncMock,
    )

    result = await get_text_detail_by_id(
        edition_id=EDITION_ID,
        text_details_request=TextDetailsRequest(size=2),
    )

    mock_pairs.assert_not_called()
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
