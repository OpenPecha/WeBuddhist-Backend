from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, status

from pecha_api.texts.texts_openpecha_api import (
    _parse_text_detail,
    fetch_text_detail,
    fetch_text_source_link,
    fetch_critical_editions,
    fetch_editions_segmentation,
    fetch_segmentation_segments,
    fetch_edition_content,
)
from pecha_api.texts.text_openpecha_response_models import (
    TextDetailResponse,
    CriticalEditionModel,
    SegmentationResponseModel,
    SegmentationSegmentResponseModel,
    EditionContentResponse,
)

TEXT_ID = "OP0001"
EDITION_ID = "ed-1"
SEGMENTATION_ID = "seg-1"

RAW_TEXT_DETAIL = {
    "id": TEXT_ID,
    "title": {"en": "Test Text"},
    "language": "en",
    "category_id": "cat-1",
    "license": "CC0",
    "contributions": [
        {
            "role": "author",
            "person_id": "p-1",
            "person_bdrc_id": "bdrc-1",
            "person_name": {"en": "Author Name"},
            "ai_id": None,
        }
    ],
    "commentaries": ["comm-1"],
    "translations": ["trans-1"],
    "bdrc": "bdrc-text-1",
    "wiki": "wiki-link",
    "date": "2020",
    "alt_titles": [{"en": "Alt Title"}],
    "commentary_of": None,
    "translation_of": None,
}

RAW_EDITIONS = [
    {"id": EDITION_ID, "type": "critical", "source": "src", "colophon": None, "incipit_title": None, "alt_incipit_titles": None}
]

RAW_SEGMENTATIONS = [
    {"id": SEGMENTATION_ID, "edition_id": EDITION_ID, "text_id": TEXT_ID}
]

RAW_SEGMENTS = {
    "items": [
        {"id": "span-1", "lines": [{"start": 0, "end": 5}]},
        {"id": "span-2", "lines": [{"start": 6, "end": 11}]},
    ],
    "has_more": False,
    "offset": 0,
    "limit": 30,
}


def _make_mock_client(status_code: int, response_data):
    """Build a mock authenticated client that returns a fixed HTTP response."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = response_data

    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(return_value=mock_response)

    mock_client = MagicMock()
    mock_client.get_async_httpx_client.return_value = mock_http_client
    mock_client._base_url = "http://test-openpecha.org"

    return mock_client


# ============================================================================
# _parse_text_detail
# ============================================================================

def test_parse_text_detail_full_data():
    """Test parsing a complete raw API response into TextDetailResponse"""
    result = _parse_text_detail(RAW_TEXT_DETAIL)

    assert isinstance(result, TextDetailResponse)
    assert result.id == TEXT_ID
    assert result.title == {"en": "Test Text"}
    assert result.language == "en"
    assert result.category_id == "cat-1"
    assert result.license == "CC0"
    assert len(result.contributions) == 1
    assert result.contributions[0].role == "author"
    assert result.contributions[0].person_id == "p-1"
    assert result.commentaries == ["comm-1"]
    assert result.translations == ["trans-1"]
    assert result.bdrc == "bdrc-text-1"
    assert result.wiki == "wiki-link"
    assert result.date == "2020"
    assert result.alt_titles == [{"en": "Alt Title"}]


def test_parse_text_detail_missing_optional_fields():
    """Test parsing a minimal raw response with missing optional fields"""
    minimal = {
        "id": TEXT_ID,
        "language": "bo",
        "category_id": "cat-2",
    }
    result = _parse_text_detail(minimal)

    assert result.id == TEXT_ID
    assert result.title == {}
    assert result.license == ""
    assert result.contributions == []
    assert result.commentaries == []
    assert result.translations == []
    assert result.bdrc is None
    assert result.wiki is None
    assert result.date is None
    assert result.alt_titles is None


def test_parse_text_detail_alt_titles_not_list_is_none():
    """Test that alt_titles is set to None when it is not a list"""
    data = {**RAW_TEXT_DETAIL, "alt_titles": "not-a-list"}
    result = _parse_text_detail(data)
    assert result.alt_titles is None


def test_parse_text_detail_null_title_becomes_empty_dict():
    """Test that a null title from the API is coerced to an empty dict"""
    data = {**RAW_TEXT_DETAIL, "title": None}
    result = _parse_text_detail(data)
    assert result.title == {}


def test_parse_text_detail_contribution_with_missing_fields():
    """Test that contribution fields default to None when absent"""
    data = {**RAW_TEXT_DETAIL, "contributions": [{"role": "editor"}]}
    result = _parse_text_detail(data)
    contrib = result.contributions[0]
    assert contrib.role == "editor"
    assert contrib.person_id is None
    assert contrib.person_bdrc_id is None
    assert contrib.person_name is None
    assert contrib.ai_id is None


# ============================================================================
# fetch_text_detail
# ============================================================================

@pytest.mark.asyncio
async def test_fetch_text_detail_success(mocker):
    """Test successful fetch returns a parsed TextDetailResponse"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(200, RAW_TEXT_DETAIL),
    )

    result = await fetch_text_detail(text_id=TEXT_ID)

    assert isinstance(result, TextDetailResponse)
    assert result.id == TEXT_ID
    assert result.language == "en"


@pytest.mark.asyncio
async def test_fetch_text_detail_404_raises_not_found(mocker):
    """Test that a 404 response raises HTTP 404"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(404, {}),
    )

    with pytest.raises(HTTPException) as exc_info:
        await fetch_text_detail(text_id=TEXT_ID)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert TEXT_ID in exc_info.value.detail


@pytest.mark.asyncio
async def test_fetch_text_detail_unexpected_status_raises_502(mocker):
    """Test that an unexpected non-200/404 status raises HTTP 502"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(500, {}),
    )

    with pytest.raises(HTTPException) as exc_info:
        await fetch_text_detail(text_id=TEXT_ID)

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY


@pytest.mark.asyncio
async def test_fetch_text_detail_network_error_raises_502(mocker):
    """Test that a network exception raises HTTP 502"""
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(side_effect=Exception("connection refused"))
    mock_client = MagicMock()
    mock_client.get_async_httpx_client.return_value = mock_http_client
    mock_client._base_url = "http://test"
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=mock_client,
    )

    with pytest.raises(HTTPException) as exc_info:
        await fetch_text_detail(text_id=TEXT_ID)

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY


# ============================================================================
# fetch_text_source_link
# ============================================================================

@pytest.mark.asyncio
async def test_fetch_text_source_link_success(mocker):
    """Test successful fetch returns source from first critical edition"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(200, [{"id": EDITION_ID, "source": "https://example.com/source"}]),
    )

    result = await fetch_text_source_link(text_id=TEXT_ID)

    assert result == "https://example.com/source"


@pytest.mark.asyncio
async def test_fetch_text_source_link_empty_list_returns_none(mocker):
    """Test that an empty editions list returns None"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(200, []),
    )

    result = await fetch_text_source_link(text_id=TEXT_ID)

    assert result is None


@pytest.mark.asyncio
async def test_fetch_text_source_link_missing_source_returns_none(mocker):
    """Test that an edition without a source field returns None"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(200, [{"id": EDITION_ID}]),
    )

    result = await fetch_text_source_link(text_id=TEXT_ID)

    assert result is None


@pytest.mark.asyncio
async def test_fetch_text_source_link_non_200_returns_none(mocker):
    """Test that a non-200 response returns None without raising"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(404, {}),
    )

    result = await fetch_text_source_link(text_id=TEXT_ID)

    assert result is None


@pytest.mark.asyncio
async def test_fetch_text_source_link_network_error_returns_none(mocker):
    """Test that a network exception returns None"""
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(side_effect=RuntimeError("timeout"))
    mock_client = MagicMock()
    mock_client.get_async_httpx_client.return_value = mock_http_client
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=mock_client,
    )

    result = await fetch_text_source_link(text_id=TEXT_ID)

    assert result is None


# ============================================================================
# fetch_critical_editions
# ============================================================================

@pytest.mark.asyncio
async def test_fetch_critical_editions_success(mocker):
    """Test successful fetch returns a list of CriticalEditionModel"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(200, RAW_EDITIONS),
    )

    result = await fetch_critical_editions(text_id=TEXT_ID)

    assert len(result) == 1
    assert isinstance(result[0], CriticalEditionModel)
    assert result[0].id == EDITION_ID
    assert result[0].type == "critical"


@pytest.mark.asyncio
async def test_fetch_critical_editions_empty_list(mocker):
    """Test that an empty response returns an empty list"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(200, []),
    )

    result = await fetch_critical_editions(text_id=TEXT_ID)

    assert result == []


@pytest.mark.asyncio
async def test_fetch_critical_editions_404_raises_not_found(mocker):
    """Test that a 404 response raises HTTP 404"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(404, {}),
    )

    with pytest.raises(HTTPException) as exc_info:
        await fetch_critical_editions(text_id=TEXT_ID)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_fetch_critical_editions_unexpected_status_raises_502(mocker):
    """Test that an unexpected status raises HTTP 502"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(503, {}),
    )

    with pytest.raises(HTTPException) as exc_info:
        await fetch_critical_editions(text_id=TEXT_ID)

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY


@pytest.mark.asyncio
async def test_fetch_critical_editions_network_error_re_raises(mocker):
    """Test that a network exception is re-raised as-is"""
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(side_effect=RuntimeError("timeout"))
    mock_client = MagicMock()
    mock_client.get_async_httpx_client.return_value = mock_http_client
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=mock_client,
    )

    with pytest.raises(RuntimeError):
        await fetch_critical_editions(text_id=TEXT_ID)


# ============================================================================
# fetch_editions_segmentation
# ============================================================================

@pytest.mark.asyncio
async def test_fetch_editions_segmentation_success(mocker):
    """Test successful fetch returns a list of SegmentationResponseModel"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(200, RAW_SEGMENTATIONS),
    )

    result = await fetch_editions_segmentation(edition_id=EDITION_ID)

    assert len(result) == 1
    assert isinstance(result[0], SegmentationResponseModel)
    assert result[0].id == SEGMENTATION_ID
    assert result[0].edition_id == EDITION_ID
    assert result[0].text_id == TEXT_ID


@pytest.mark.asyncio
async def test_fetch_editions_segmentation_404_raises_not_found(mocker):
    """Test that a 404 response raises HTTP 404"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(404, {}),
    )

    with pytest.raises(HTTPException) as exc_info:
        await fetch_editions_segmentation(edition_id=EDITION_ID)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert EDITION_ID in exc_info.value.detail


@pytest.mark.asyncio
async def test_fetch_editions_segmentation_unexpected_status_raises_502(mocker):
    """Test that an unexpected status raises HTTP 502"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(500, {}),
    )

    with pytest.raises(HTTPException) as exc_info:
        await fetch_editions_segmentation(edition_id=EDITION_ID)

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY


@pytest.mark.asyncio
async def test_fetch_editions_segmentation_network_error_re_raises(mocker):
    """Test that a network exception is re-raised as-is"""
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(side_effect=ConnectionError("refused"))
    mock_client = MagicMock()
    mock_client.get_async_httpx_client.return_value = mock_http_client
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=mock_client,
    )

    with pytest.raises(ConnectionError):
        await fetch_editions_segmentation(edition_id=EDITION_ID)


# ============================================================================
# fetch_segmentation_segments
# ============================================================================

@pytest.mark.asyncio
async def test_fetch_segmentation_segments_success(mocker):
    """Test successful fetch returns a parsed SegmentationSegmentResponseModel"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(200, RAW_SEGMENTS),
    )

    result = await fetch_segmentation_segments(segmentation_id=SEGMENTATION_ID, limit=30, offset=0)

    assert isinstance(result, SegmentationSegmentResponseModel)
    assert len(result.items) == 2
    assert result.items[0].id == "span-1"
    assert result.items[0].lines[0].start == 0
    assert result.items[0].lines[0].end == 5
    assert result.has_more is False
    assert result.offset == 0
    assert result.limit == 30


@pytest.mark.asyncio
async def test_fetch_segmentation_segments_empty_items(mocker):
    """Test response with empty items list"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(200, {"items": [], "has_more": False, "offset": 0, "limit": 30}),
    )

    result = await fetch_segmentation_segments(segmentation_id=SEGMENTATION_ID, limit=30, offset=0)

    assert result.items == []
    assert result.has_more is False


@pytest.mark.asyncio
async def test_fetch_segmentation_segments_404_raises_not_found(mocker):
    """Test that a 404 response raises HTTP 404"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(404, {}),
    )

    with pytest.raises(HTTPException) as exc_info:
        await fetch_segmentation_segments(segmentation_id=SEGMENTATION_ID, limit=30, offset=0)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert SEGMENTATION_ID in exc_info.value.detail


@pytest.mark.asyncio
async def test_fetch_segmentation_segments_unexpected_status_raises_502(mocker):
    """Test that an unexpected status raises HTTP 502"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(503, {}),
    )

    with pytest.raises(HTTPException) as exc_info:
        await fetch_segmentation_segments(segmentation_id=SEGMENTATION_ID, limit=30, offset=0)

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY


@pytest.mark.asyncio
async def test_fetch_segmentation_segments_network_error_raises_502(mocker):
    """Test that a network exception raises HTTP 502"""
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(side_effect=Exception("timeout"))
    mock_client = MagicMock()
    mock_client.get_async_httpx_client.return_value = mock_http_client
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=mock_client,
    )

    with pytest.raises(HTTPException) as exc_info:
        await fetch_segmentation_segments(segmentation_id=SEGMENTATION_ID, limit=30, offset=0)

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY


# ============================================================================
# fetch_edition_content
# ============================================================================

@pytest.mark.asyncio
async def test_fetch_edition_content_success(mocker):
    """Test successful fetch returns an EditionContentResponse"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(200, "Hello World content"),
    )

    result = await fetch_edition_content(edition_id=EDITION_ID)

    assert isinstance(result, EditionContentResponse)
    assert result.content == "Hello World content"


@pytest.mark.asyncio
async def test_fetch_edition_content_404_raises_not_found(mocker):
    """Test that a 404 response raises HTTP 404"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(404, {}),
    )

    with pytest.raises(HTTPException) as exc_info:
        await fetch_edition_content(edition_id=EDITION_ID)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert EDITION_ID in exc_info.value.detail


@pytest.mark.asyncio
async def test_fetch_edition_content_unexpected_status_raises_502(mocker):
    """Test that an unexpected status raises HTTP 502"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=_make_mock_client(500, {}),
    )

    with pytest.raises(HTTPException) as exc_info:
        await fetch_edition_content(edition_id=EDITION_ID)

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY


@pytest.mark.asyncio
async def test_fetch_edition_content_network_error_raises_502(mocker):
    """Test that a network exception raises HTTP 502"""
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(side_effect=Exception("connection reset"))
    mock_client = MagicMock()
    mock_client.get_async_httpx_client.return_value = mock_http_client
    mocker.patch(
        "pecha_api.texts.texts_openpecha_api.get_authenticated_open_pecha_client",
        return_value=mock_client,
    )

    with pytest.raises(HTTPException) as exc_info:
        await fetch_edition_content(edition_id=EDITION_ID)

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY
