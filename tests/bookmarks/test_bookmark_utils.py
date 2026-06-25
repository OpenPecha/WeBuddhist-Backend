import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from pecha_api.bookmarks.bookmark_enums import BookmarkType
from pecha_api.bookmarks.bookmark_utils import (
    _resolve_segment_by_ref,
    _resolve_text_segment,
    enrich_text_bookmark,
)


@pytest.mark.asyncio
async def test_resolve_segment_by_ref_with_uuid():
    segment_id = str(uuid4())
    mock_segment = MagicMock()

    with patch(
        "pecha_api.bookmarks.bookmark_utils.get_segment_by_id",
        new_callable=AsyncMock,
        return_value=mock_segment,
    ):
        result = await _resolve_segment_by_ref(segment_id)

    assert result is mock_segment


@pytest.mark.asyncio
async def test_resolve_segment_by_ref_with_pecha_id_when_uuid_lookup_fails():
    mock_segment = MagicMock()

    with patch(
        "pecha_api.bookmarks.bookmark_utils.get_segment_by_id",
        new_callable=AsyncMock,
        return_value=None,
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.Segment.get_segment_by_pecha_segment_id",
        new_callable=AsyncMock,
        return_value=mock_segment,
    ) as mock_pecha_lookup:
        result = await _resolve_segment_by_ref(str(uuid4()))

    mock_pecha_lookup.assert_awaited_once()
    assert result is mock_segment


@pytest.mark.asyncio
async def test_resolve_segment_by_ref_with_non_uuid_uses_pecha_lookup():
    verse_locator = "segment-ref-abc-123"
    mock_segment = MagicMock()

    with patch(
        "pecha_api.bookmarks.bookmark_utils.Segment.get_segment_by_pecha_segment_id",
        new_callable=AsyncMock,
        return_value=mock_segment,
    ) as mock_pecha_lookup:
        result = await _resolve_segment_by_ref(verse_locator)

    mock_pecha_lookup.assert_awaited_once_with(pecha_segment_id=verse_locator)
    assert result is mock_segment


@pytest.mark.asyncio
async def test_resolve_text_segment_with_matching_verse_id():
    text_id = str(uuid4())
    segment_id = str(uuid4())
    mock_segment = MagicMock()
    mock_segment.id = segment_id
    mock_segment.text_id = text_id

    with patch(
        "pecha_api.bookmarks.bookmark_utils._resolve_segment_by_ref",
        new_callable=AsyncMock,
        return_value=mock_segment,
    ):
        resolved_id, resolved_segment = await _resolve_text_segment(
            text_id=text_id,
            verse_id=segment_id,
        )

    assert resolved_id == segment_id
    assert resolved_segment is mock_segment


@pytest.mark.asyncio
async def test_resolve_text_segment_ignores_verse_from_other_text():
    text_id = str(uuid4())
    segment_id = str(uuid4())
    mock_segment = MagicMock()
    mock_segment.id = segment_id
    mock_segment.text_id = str(uuid4())

    fallback_segment = MagicMock()
    fallback_segment.id = str(uuid4())

    with patch(
        "pecha_api.bookmarks.bookmark_utils._resolve_segment_by_ref",
        new_callable=AsyncMock,
        return_value=mock_segment,
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.get_first_segment_table_of_content",
        new_callable=AsyncMock,
        return_value=(str(fallback_segment.id), None),
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.get_segment_by_id",
        new_callable=AsyncMock,
        return_value=fallback_segment,
    ):
        resolved_id, resolved_segment = await _resolve_text_segment(
            text_id=text_id,
            verse_id=segment_id,
        )

    assert resolved_id == str(fallback_segment.id)
    assert resolved_segment is fallback_segment


@pytest.mark.asyncio
async def test_resolve_text_segment_falls_back_to_first_segment_by_text_id():
    text_id = str(uuid4())
    mock_segment = MagicMock()
    mock_segment.id = str(uuid4())

    with patch(
        "pecha_api.bookmarks.bookmark_utils.get_first_segment_table_of_content",
        new_callable=AsyncMock,
        return_value=(None, None),
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.Segment.get_first_segment_by_text_id",
        new_callable=AsyncMock,
        return_value=mock_segment,
    ):
        resolved_id, resolved_segment = await _resolve_text_segment(
            text_id=text_id,
            verse_id=None,
        )

    assert resolved_id == str(mock_segment.id)
    assert resolved_segment is mock_segment


@pytest.mark.asyncio
async def test_resolve_text_segment_returns_none_when_not_found():
    text_id = str(uuid4())

    with patch(
        "pecha_api.bookmarks.bookmark_utils.get_first_segment_table_of_content",
        new_callable=AsyncMock,
        return_value=(None, None),
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.Segment.get_first_segment_by_text_id",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resolved_id, resolved_segment = await _resolve_text_segment(
            text_id=text_id,
            verse_id=None,
        )

    assert resolved_id is None
    assert resolved_segment is None


@pytest.mark.asyncio
async def test_enrich_text_bookmark_without_verse_uses_first_segment():
    text_id = str(uuid4())
    segment_id = str(uuid4())

    bookmark = MagicMock()
    bookmark.type = BookmarkType.TEXT
    bookmark.source_id = text_id
    bookmark.name = None

    mock_text = MagicMock()
    mock_text.title = "Heart Sutra"

    mock_segment = MagicMock()
    mock_segment.id = segment_id
    mock_segment.text_id = text_id
    mock_segment.content = "Segment content"

    with patch(
        "pecha_api.bookmarks.bookmark_utils.get_first_segment_table_of_content",
        new_callable=AsyncMock,
        return_value=(segment_id, None),
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.get_segment_by_id",
        new_callable=AsyncMock,
        return_value=mock_segment,
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.get_texts_by_id",
        new_callable=AsyncMock,
        return_value=mock_text,
    ):
        result = await enrich_text_bookmark(bookmark)

    assert result["text_id"] == text_id
    assert result["text_title"] == "Heart Sutra"
    assert result["segment_id"] == segment_id
    assert result["segment_content"] == "Segment content"
    assert "verse_id" not in result


@pytest.mark.asyncio
async def test_enrich_text_bookmark_with_name_as_segment_ref():
    text_id = str(uuid4())
    segment_id = str(uuid4())
    verse_locator = "segment-ref-abc-123"

    bookmark = MagicMock()
    bookmark.type = BookmarkType.TEXT
    bookmark.source_id = text_id
    bookmark.name = verse_locator

    mock_text = MagicMock()
    mock_text.title = "Heart Sutra"

    mock_segment = MagicMock()
    mock_segment.id = segment_id
    mock_segment.text_id = text_id
    mock_segment.content = "Named segment content"

    with patch(
        "pecha_api.bookmarks.bookmark_utils._resolve_segment_by_ref",
        new_callable=AsyncMock,
        return_value=mock_segment,
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.get_texts_by_id",
        new_callable=AsyncMock,
        return_value=mock_text,
    ):
        result = await enrich_text_bookmark(bookmark)

    assert result["verse_id"] == verse_locator
    assert result["segment_content"] == "Named segment content"


@pytest.mark.asyncio
async def test_enrich_text_bookmark_returns_empty_when_segment_missing():
    text_id = str(uuid4())

    bookmark = MagicMock()
    bookmark.type = BookmarkType.TEXT
    bookmark.source_id = text_id
    bookmark.name = None

    with patch(
        "pecha_api.bookmarks.bookmark_utils._resolve_text_segment",
        new_callable=AsyncMock,
        return_value=(None, None),
    ):
        result = await enrich_text_bookmark(bookmark)

    assert result == {}


@pytest.mark.asyncio
async def test_enrich_verse_bookmark_includes_segment_content():
    text_id = str(uuid4())
    segment_id = str(uuid4())
    verse_locator = "segment-ref-abc-123"

    bookmark = MagicMock()
    bookmark.type = BookmarkType.VERSE
    bookmark.source_id = verse_locator
    bookmark.name = None

    mock_text = MagicMock()
    mock_text.title = "Lotus Sutra"

    mock_segment = MagicMock()
    mock_segment.id = segment_id
    mock_segment.text_id = text_id
    mock_segment.content = "Verse segment content"

    with patch(
        "pecha_api.bookmarks.bookmark_utils._resolve_segment_by_ref",
        new_callable=AsyncMock,
        return_value=mock_segment,
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.get_texts_by_id",
        new_callable=AsyncMock,
        return_value=mock_text,
    ):
        result = await enrich_text_bookmark(bookmark)

    assert result["text_id"] == text_id
    assert result["text_title"] == "Lotus Sutra"
    assert result["segment_id"] == segment_id
    assert result["segment_content"] == "Verse segment content"
    assert result["verse_id"] == verse_locator


@pytest.mark.asyncio
async def test_enrich_verse_bookmark_returns_empty_when_segment_not_found():
    bookmark = MagicMock()
    bookmark.type = BookmarkType.VERSE
    bookmark.source_id = "missing-ref"
    bookmark.name = None

    with patch(
        "pecha_api.bookmarks.bookmark_utils._resolve_segment_by_ref",
        new_callable=AsyncMock,
        return_value=None,
    ):
        result = await enrich_text_bookmark(bookmark)

    assert result == {}


@pytest.mark.asyncio
async def test_enrich_unsupported_bookmark_type_returns_empty():
    bookmark = MagicMock()
    bookmark.type = BookmarkType.PLAN
    bookmark.source_id = str(uuid4())

    result = await enrich_text_bookmark(bookmark)

    assert result == {}


@pytest.mark.asyncio
async def test_enrich_text_bookmark_handles_missing_text_details():
    text_id = str(uuid4())
    segment_id = str(uuid4())

    bookmark = MagicMock()
    bookmark.type = BookmarkType.TEXT
    bookmark.source_id = text_id
    bookmark.name = None

    mock_segment = MagicMock()
    mock_segment.id = segment_id
    mock_segment.content = "Segment content"

    with patch(
        "pecha_api.bookmarks.bookmark_utils._resolve_text_segment",
        new_callable=AsyncMock,
        return_value=(segment_id, mock_segment),
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.get_texts_by_id",
        new_callable=AsyncMock,
        return_value=None,
    ):
        result = await enrich_text_bookmark(bookmark)

    assert result["text_id"] == text_id
    assert result["text_title"] is None
    assert result["segment_content"] == "Segment content"
