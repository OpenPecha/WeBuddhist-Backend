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


@pytest.mark.asyncio
async def test_enrich_text_bookmark_with_language_uses_localized_text():
    text_id = str(uuid4())
    localized_text_id = str(uuid4())
    segment_id = str(uuid4())

    bookmark = MagicMock()
    bookmark.type = BookmarkType.TEXT
    bookmark.source_id = text_id
    bookmark.name = None

    mock_segment = MagicMock()
    mock_segment.id = segment_id
    mock_segment.text_id = text_id
    mock_segment.content = "English content"

    localized_text = MagicMock()
    localized_text.id = localized_text_id
    localized_text.title = "བོད་ཡིག་ཁ་བྱང་"

    with patch(
        "pecha_api.bookmarks.bookmark_utils._resolve_text_segment",
        new_callable=AsyncMock,
        return_value=(segment_id, mock_segment),
    ), patch(
        "pecha_api.bookmarks.bookmark_utils._resolve_localized_text",
        new_callable=AsyncMock,
        return_value=localized_text,
    ), patch(
        "pecha_api.bookmarks.bookmark_utils._resolve_localized_segment",
        new_callable=AsyncMock,
        return_value=mock_segment,
    ):
        result = await enrich_text_bookmark(bookmark, language="BO")

    assert result["text_id"] == localized_text_id
    assert result["text_title"] == "བོད་ཡིག་ཁ་བྱང་"


def test_enrich_plan_bookmark_with_language_uses_matching_sibling():
    from pecha_api.bookmarks.bookmark_utils import enrich_plan_bookmark

    source_plan_id = uuid4()
    bo_plan_id = uuid4()
    mock_db = MagicMock()

    source_plan = MagicMock()
    source_plan.id = source_plan_id
    source_plan.series_id = uuid4()
    source_plan.display_order = 1
    source_plan.language = MagicMock(value="EN")

    bo_plan = MagicMock()
    bo_plan.id = bo_plan_id
    bo_plan.title = "བོད་ཡིག་ཐེངས་"
    bo_plan.description = "བོད་ཡིག་ཞབས་ཞུ་"
    bo_plan.language = MagicMock(value="BO")
    bo_plan.difficulty_level = None
    bo_plan.image_url = None
    bo_plan.author = None
    bo_plan.start_date = None
    bo_plan.display_order = 1
    bo_plan.tag_list = []

    with patch(
        "pecha_api.bookmarks.bookmark_utils.get_published_plan_by_id",
        side_effect=lambda db, plan_id: source_plan if plan_id == source_plan_id else bo_plan,
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.get_sibling_plans_in_series_slot",
        return_value=[bo_plan],
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.get_group_id_for_plan",
        return_value=None,
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.get_image_url",
        return_value=None,
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.tags_to_summary_dtos",
        return_value=[],
    ):
        mock_db.query.return_value.filter.return_value.count.return_value = 3
        result = enrich_plan_bookmark(
            db=mock_db,
            source_id=str(source_plan_id),
            language="BO",
        )

    assert result["plan"].id == bo_plan_id
    assert result["plan"].title == "བོད་ཡིག་ཐེངས་"
    assert result["plan"].language == "BO"


def test_enrich_plan_bookmark_returns_empty_for_invalid_source_id():
    from pecha_api.bookmarks.bookmark_utils import enrich_plan_bookmark

    result = enrich_plan_bookmark(db=MagicMock(), source_id="not-a-uuid")

    assert result == {}


def test_enrich_plan_bookmark_returns_empty_when_plan_not_found():
    from pecha_api.bookmarks.bookmark_utils import enrich_plan_bookmark

    with patch(
        "pecha_api.bookmarks.bookmark_utils.get_published_plan_by_id",
        return_value=None,
    ):
        result = enrich_plan_bookmark(
            db=MagicMock(),
            source_id=str(uuid4()),
        )

    assert result == {}


def test_enrich_plan_bookmark_includes_author_details():
    from pecha_api.bookmarks.bookmark_utils import enrich_plan_bookmark

    plan_id = uuid4()
    author_id = uuid4()
    mock_db = MagicMock()

    mock_plan = MagicMock()
    mock_plan.id = plan_id
    mock_plan.title = "Morning Practice"
    mock_plan.description = "Daily practice"
    mock_plan.language = "EN"
    mock_plan.difficulty_level = None
    mock_plan.image_url = "plan.png"
    mock_plan.start_date = None
    mock_plan.display_order = None
    mock_plan.tag_list = []
    mock_plan.author = MagicMock()
    mock_plan.author.id = author_id
    mock_plan.author.first_name = "Tenzin"
    mock_plan.author.last_name = "Gyatso"
    mock_plan.author.image_url = "author.png"

    with patch(
        "pecha_api.bookmarks.bookmark_utils.get_published_plan_by_id",
        return_value=mock_plan,
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.get_group_id_for_plan",
        return_value=None,
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.get_image_url",
        return_value=None,
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.tags_to_summary_dtos",
        return_value=[],
    ):
        mock_db.query.return_value.filter.return_value.count.return_value = 7
        result = enrich_plan_bookmark(db=mock_db, source_id=str(plan_id))

    assert result["plan"].id == plan_id
    assert result["plan"].author.firstname == "Tenzin"
    assert result["plan"].author.lastname == "Gyatso"
    assert result["plan"].total_days == 7


def test_enrich_series_bookmark_success():
    from pecha_api.bookmarks.bookmark_utils import enrich_series_bookmark

    series_id = uuid4()
    mock_db = MagicMock()
    mock_series = MagicMock()
    mock_series.status = "PUBLISHED"
    mock_series.plans = []
    mock_dto = MagicMock()

    with patch(
        "pecha_api.bookmarks.bookmark_utils.get_series_by_id",
        return_value=mock_series,
    ), patch(
        "pecha_api.bookmarks.bookmark_utils._to_plan_status",
        return_value=__import__(
            "pecha_api.plans.plans_enums", fromlist=["PlanStatus"]
        ).PlanStatus.PUBLISHED,
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.get_active_plan_count_map_by_series_ids",
        return_value={series_id: 2},
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.get_enrolled_count_map_by_series_ids",
        return_value={series_id: 5},
    ), patch(
        "pecha_api.bookmarks.bookmark_utils._series_schedule_from_plans",
        return_value=(None, None, 10),
    ), patch(
        "pecha_api.bookmarks.bookmark_utils._group_summary_for_series",
        return_value=None,
    ), patch(
        "pecha_api.bookmarks.bookmark_utils._series_to_list_item_dto",
        return_value=mock_dto,
    ):
        result = enrich_series_bookmark(
            db=mock_db,
            source_id=str(series_id),
            language="BO",
        )

    assert result == {"series": mock_dto}


def test_enrich_series_bookmark_returns_empty_when_unpublished():
    from pecha_api.bookmarks.bookmark_utils import enrich_series_bookmark
    from pecha_api.plans.plans_enums import PlanStatus

    series_id = uuid4()

    with patch(
        "pecha_api.bookmarks.bookmark_utils.get_series_by_id",
        return_value=MagicMock(),
    ), patch(
        "pecha_api.bookmarks.bookmark_utils._to_plan_status",
        return_value=PlanStatus.DRAFT,
    ):
        result = enrich_series_bookmark(db=MagicMock(), source_id=str(series_id))

    assert result == {}


def test_enrich_accumulator_bookmark_success():
    from pecha_api.bookmarks.bookmark_utils import enrich_accumulator_bookmark

    accumulator_id = uuid4()
    mock_db = MagicMock()
    mock_accumulator = MagicMock()
    mock_accumulator.metadata_entries = []
    mock_dto = MagicMock()

    mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = (
        mock_accumulator
    )

    with patch(
        "pecha_api.bookmarks.bookmark_utils.convert_accumulator_to_dto",
        return_value=mock_dto,
    ):
        result = enrich_accumulator_bookmark(
            db=mock_db,
            source_id=str(accumulator_id),
        )

    assert result == {"accumulator": mock_dto}


def test_enrich_accumulator_bookmark_filters_metadata_by_language():
    from pecha_api.bookmarks.bookmark_utils import enrich_accumulator_bookmark

    accumulator_id = uuid4()
    mock_db = MagicMock()
    mock_accumulator = MagicMock()
    metadata_entry = MagicMock()
    mock_accumulator.metadata_entries = [metadata_entry]
    mock_dto = MagicMock()

    mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = (
        mock_accumulator
    )

    with patch(
        "pecha_api.bookmarks.bookmark_utils.convert_accumulator_to_dto",
        return_value=mock_dto,
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.filter_by_language_with_fallback",
        return_value=[metadata_entry],
    ) as mock_filter, patch(
        "pecha_api.bookmarks.bookmark_utils.convert_metadata_to_dto",
        return_value=MagicMock(),
    ) as mock_metadata_dto:
        result = enrich_accumulator_bookmark(
            db=mock_db,
            source_id=str(accumulator_id),
            language="BO",
        )

    mock_filter.assert_called_once()
    mock_metadata_dto.assert_called_once_with(metadata_entry)
    assert result == {"accumulator": mock_dto}
    assert mock_dto.metadata == [mock_metadata_dto.return_value]


def test_enrich_timer_bookmark_success():
    from pecha_api.bookmarks.bookmark_utils import enrich_timer_bookmark

    timer_id = uuid4()
    mock_timer = MagicMock()
    mock_dto = MagicMock()

    with patch(
        "pecha_api.bookmarks.bookmark_utils.get_timer_by_id",
        return_value=mock_timer,
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.convert_timer_to_dto",
        return_value=mock_dto,
    ):
        result = enrich_timer_bookmark(db=MagicMock(), source_id=str(timer_id))

    assert result == {"timer": mock_dto}


def test_enrich_timer_bookmark_returns_empty_when_not_found():
    from pecha_api.bookmarks.bookmark_utils import enrich_timer_bookmark

    with patch(
        "pecha_api.bookmarks.bookmark_utils.get_timer_by_id",
        return_value=None,
    ):
        result = enrich_timer_bookmark(db=MagicMock(), source_id=str(uuid4()))

    assert result == {}


@pytest.mark.asyncio
async def test_resolve_localized_text_returns_matching_group_text():
    from pecha_api.bookmarks.bookmark_utils import _resolve_localized_text

    text_id = str(uuid4())
    localized_text = MagicMock()
    localized_text.language = "BO"

    source_text = MagicMock()
    source_text.group_id = uuid4()

    with patch(
        "pecha_api.bookmarks.bookmark_utils.get_texts_by_id",
        new_callable=AsyncMock,
        return_value=source_text,
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.get_all_texts_by_group_id",
        new_callable=AsyncMock,
        return_value=[localized_text],
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.filter_by_language_with_fallback",
        return_value=[localized_text],
    ):
        result = await _resolve_localized_text(text_id=text_id, language="BO")

    assert result is localized_text


@pytest.mark.asyncio
async def test_resolve_localized_segment_returns_mapped_segment():
    from pecha_api.bookmarks.bookmark_utils import _resolve_localized_segment

    target_text_id = str(uuid4())
    segment = MagicMock()
    segment.text_id = str(uuid4())
    segment.id = uuid4()

    mapped = MagicMock()
    mapped.text_id = target_text_id
    mapped.id = uuid4()
    localized = MagicMock()

    with patch(
        "pecha_api.bookmarks.bookmark_utils.get_related_mapped_segments",
        new_callable=AsyncMock,
        return_value=[mapped],
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.get_segment_by_id",
        new_callable=AsyncMock,
        return_value=localized,
    ):
        result = await _resolve_localized_segment(
            segment=segment,
            target_text_id=target_text_id,
        )

    assert result is localized


@pytest.mark.asyncio
async def test_enrich_text_bookmark_falls_back_when_localized_text_missing():
    text_id = str(uuid4())
    segment_id = str(uuid4())

    bookmark = MagicMock()
    bookmark.type = BookmarkType.TEXT
    bookmark.source_id = text_id
    bookmark.name = None

    mock_segment = MagicMock()
    mock_segment.id = segment_id
    mock_segment.text_id = text_id
    mock_segment.content = "Fallback content"

    mock_text = MagicMock()
    mock_text.title = "Original title"

    with patch(
        "pecha_api.bookmarks.bookmark_utils._resolve_text_segment",
        new_callable=AsyncMock,
        return_value=(segment_id, mock_segment),
    ), patch(
        "pecha_api.bookmarks.bookmark_utils._resolve_localized_text",
        new_callable=AsyncMock,
        return_value=None,
    ), patch(
        "pecha_api.bookmarks.bookmark_utils.get_texts_by_id",
        new_callable=AsyncMock,
        return_value=mock_text,
    ):
        result = await enrich_text_bookmark(bookmark, language="BO")

    assert result["text_title"] == "Original title"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bookmark_type,patch_target",
    [
        (BookmarkType.TEXT, "enrich_text_bookmark"),
        (BookmarkType.VERSE, "enrich_text_bookmark"),
        (BookmarkType.PLAN, "enrich_plan_bookmark"),
        (BookmarkType.SERIES, "enrich_series_bookmark"),
        (BookmarkType.ACCUMULATOR, "enrich_accumulator_bookmark"),
        (BookmarkType.TIMER, "enrich_timer_bookmark"),
    ],
)
async def test_enrich_bookmark_dispatches_by_type(bookmark_type, patch_target):
    from pecha_api.bookmarks import bookmark_utils

    bookmark = MagicMock()
    bookmark.type = bookmark_type
    bookmark.source_id = str(uuid4())
    mock_db = MagicMock()
    expected = {"key": "value"}

    if bookmark_type in (BookmarkType.TEXT, BookmarkType.VERSE):
        with patch.object(
            bookmark_utils,
            patch_target,
            new_callable=AsyncMock,
            return_value=expected,
        ) as mock_enrich:
            result = await bookmark_utils.enrich_bookmark(
                bookmark=bookmark,
                db=mock_db,
                language=" bo ",
            )
        mock_enrich.assert_awaited_once_with(bookmark, language="BO")
    elif bookmark_type == BookmarkType.TIMER:
        with patch.object(
            bookmark_utils,
            patch_target,
            return_value=expected,
        ) as mock_enrich:
            result = await bookmark_utils.enrich_bookmark(
                bookmark=bookmark,
                db=mock_db,
                language="EN",
            )
        mock_enrich.assert_called_once_with(
            db=mock_db,
            source_id=bookmark.source_id,
        )
    else:
        with patch.object(
            bookmark_utils,
            patch_target,
            return_value=expected,
        ) as mock_enrich:
            result = await bookmark_utils.enrich_bookmark(
                bookmark=bookmark,
                db=mock_db,
                language="EN",
            )
        mock_enrich.assert_called_once_with(
            db=mock_db,
            source_id=bookmark.source_id,
            language="EN",
        )

    assert result == expected


@pytest.mark.asyncio
async def test_enrich_bookmark_returns_empty_for_unknown_type():
    from pecha_api.bookmarks.bookmark_utils import enrich_bookmark

    bookmark = MagicMock()
    bookmark.type = "UNKNOWN"

    result = await enrich_bookmark(bookmark=bookmark, db=MagicMock())

    assert result == {}

