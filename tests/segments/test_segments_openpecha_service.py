import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

from pecha_api.texts.segments.segments_openpecha_service import (
    _classify_text,
    get_commentaries_by_segment_id_from_openpecha,
    get_root_text_by_segment_id_from_openpecha,
    get_translations_by_segment_id_from_openpecha,
)
from pecha_api.texts.segments.segments_response_models import (
    V2SegmentCommentariesResponse,
    V2SegmentRootTextResponse,
    V2SegmentTranslationsResponse,
)

PARENT_SEGMENT_ID = "parent-seg-1"
TRANSLATION_TEXT_ID = "text-trans-1"
COMMENTARY_TEXT_ID = "text-comm-1"
ROOT_TEXT_ID = "1AIZhR8IBkX4WMfNYkmpc"


def _translation_text(text_id: str) -> dict:
    return {
        "id": text_id,
        "title": {"en": f"Translation {text_id}"},
        "language": "en",
        "translation_of": "root-text-id",
        "commentary_of": None,
    }


def _commentary_text(text_id: str) -> dict:
    return {
        "id": text_id,
        "title": {"en": f"Commentary {text_id}"},
        "language": "bo",
        "translation_of": None,
        "commentary_of": "root-text-id",
    }


def _root_text(text_id: str) -> dict:
    return {
        "id": text_id,
        "title": {"bo": f"Root text {text_id}"},
        "language": "bo",
        "translation_of": None,
        "commentary_of": None,
    }


def _related_item(segment_id: str, text_id: str) -> dict:
    return {
        "id": segment_id,
        "text_id": text_id,
        "edition_id": "edition-1",
        "segmentation_id": "seg-1",
        "lines": [{"start": 0, "end": 10}],
        "tag_ids": None,
    }


def _related_page(items: list, has_more: bool = False, offset: int = 0, limit: int = 10) -> dict:
    return {
        "items": items,
        "has_more": has_more,
        "offset": offset,
        "limit": limit,
    }


class TestClassifyText:
    def test_classifies_translation(self):
        assert _classify_text(_translation_text("t1")) == "translation"

    def test_classifies_commentary(self):
        assert _classify_text(_commentary_text("t1")) == "commentary"

    def test_returns_none_for_unrelated_text(self):
        assert _classify_text({"id": "t1", "translation_of": None, "commentary_of": None}) is None

    def test_returns_none_for_empty_payload(self):
        assert _classify_text({}) is None
        assert _classify_text(None) is None


class TestGetTranslationsBySegmentIdFromOpenpecha:
    @pytest.mark.asyncio
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_text_by_id",
        new_callable=AsyncMock,
    )
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_segment_content",
        new_callable=AsyncMock,
    )
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_related_segments",
        new_callable=AsyncMock,
    )
    async def test_returns_translations_grouped_by_text_id(
        self,
        mock_fetch_related,
        mock_fetch_content,
        mock_fetch_text,
    ):
        mock_fetch_related.return_value = _related_page(
            [
                _related_item("seg-trans-1", TRANSLATION_TEXT_ID),
                _related_item("seg-trans-2", TRANSLATION_TEXT_ID),
                _related_item("seg-comm-1", COMMENTARY_TEXT_ID),
            ],
            has_more=True,
        )

        async def content_side_effect(segment_id: str):
            return {
                PARENT_SEGMENT_ID: "Parent segment content",
                "seg-trans-1": "Translation segment 1",
                "seg-trans-2": "Translation segment 2",
                "seg-comm-1": "Commentary segment 1",
            }.get(segment_id)

        mock_fetch_content.side_effect = content_side_effect

        async def text_side_effect(text_id: str):
            if text_id == TRANSLATION_TEXT_ID:
                return _translation_text(text_id)
            if text_id == COMMENTARY_TEXT_ID:
                return _commentary_text(text_id)
            return None

        mock_fetch_text.side_effect = text_side_effect

        result = await get_translations_by_segment_id_from_openpecha(
            segment_id=PARENT_SEGMENT_ID,
            skip=0,
            limit=10,
        )

        assert isinstance(result, V2SegmentTranslationsResponse)
        assert result.parent_segment.segment_id == PARENT_SEGMENT_ID
        assert result.parent_segment.content == "Parent segment content"
        assert len(result.translations) == 1
        assert result.translations[0].text_id == TRANSLATION_TEXT_ID
        assert result.translations[0].title == f"Translation {TRANSLATION_TEXT_ID}"
        assert result.translations[0].language == "en"
        assert len(result.translations[0].segments) == 2
        assert result.translations[0].segments[0].id == "seg-trans-1"
        assert result.translations[0].segments[0].content == "Translation segment 1"
        assert result.translations[0].segments[1].id == "seg-trans-2"
        assert result.skip == 0
        assert result.limit == 10
        assert result.has_more is True

        mock_fetch_related.assert_awaited_once_with(
            segment_id=PARENT_SEGMENT_ID,
            limit=10,
            offset=0,
        )

    @pytest.mark.asyncio
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_text_by_id",
        new_callable=AsyncMock,
    )
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_segment_content",
        new_callable=AsyncMock,
    )
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_related_segments",
        new_callable=AsyncMock,
    )
    async def test_returns_empty_translations_when_no_related_items(
        self,
        mock_fetch_related,
        mock_fetch_content,
        mock_fetch_text,
    ):
        mock_fetch_related.return_value = _related_page([])
        mock_fetch_content.return_value = "Parent content"

        result = await get_translations_by_segment_id_from_openpecha(
            segment_id=PARENT_SEGMENT_ID,
        )

        assert result.translations == []
        assert result.has_more is False
        mock_fetch_text.assert_not_awaited()

    @pytest.mark.asyncio
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_text_by_id",
        new_callable=AsyncMock,
    )
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_segment_content",
        new_callable=AsyncMock,
    )
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_related_segments",
        new_callable=AsyncMock,
    )
    async def test_returns_empty_translations_when_only_commentaries_present(
        self,
        mock_fetch_related,
        mock_fetch_content,
        mock_fetch_text,
    ):
        mock_fetch_related.return_value = _related_page(
            [_related_item("seg-comm-1", COMMENTARY_TEXT_ID)]
        )
        mock_fetch_content.return_value = "Parent content"
        mock_fetch_text.return_value = _commentary_text(COMMENTARY_TEXT_ID)

        result = await get_translations_by_segment_id_from_openpecha(
            segment_id=PARENT_SEGMENT_ID,
        )

        assert result.translations == []

    @pytest.mark.asyncio
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_segment_content",
        new_callable=AsyncMock,
    )
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_related_segments",
        new_callable=AsyncMock,
    )
    async def test_parent_segment_not_found_returns_404(
        self,
        mock_fetch_related,
        mock_fetch_content,
    ):
        mock_fetch_related.return_value = _related_page([])
        mock_fetch_content.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_translations_by_segment_id_from_openpecha(
                segment_id="missing-segment",
            )

        assert exc_info.value.status_code == 404
        assert "missing-segment" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_segment_content",
        new_callable=AsyncMock,
    )
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_related_segments",
        new_callable=AsyncMock,
    )
    async def test_upstream_related_segments_failure_returns_502(
        self,
        mock_fetch_related,
        mock_fetch_content,
    ):
        mock_fetch_content.return_value = "Parent content"
        mock_fetch_related.side_effect = Exception("connection refused")

        with pytest.raises(HTTPException) as exc_info:
            await get_translations_by_segment_id_from_openpecha(
                segment_id=PARENT_SEGMENT_ID,
            )

        assert exc_info.value.status_code == 502
        assert "upstream" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_text_by_id",
        new_callable=AsyncMock,
    )
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_segment_content",
        new_callable=AsyncMock,
    )
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_related_segments",
        new_callable=AsyncMock,
    )
    async def test_passes_skip_and_limit_to_upstream(
        self,
        mock_fetch_related,
        mock_fetch_content,
        mock_fetch_text,
    ):
        mock_fetch_related.return_value = _related_page([], offset=5, limit=3)
        mock_fetch_content.return_value = "Parent content"

        result = await get_translations_by_segment_id_from_openpecha(
            segment_id=PARENT_SEGMENT_ID,
            skip=5,
            limit=3,
        )

        assert result.skip == 5
        assert result.limit == 3
        mock_fetch_related.assert_awaited_once_with(
            segment_id=PARENT_SEGMENT_ID,
            limit=3,
            offset=5,
        )
        mock_fetch_text.assert_not_awaited()


class TestGetCommentariesBySegmentIdFromOpenpecha:
    @pytest.mark.asyncio
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_text_by_id",
        new_callable=AsyncMock,
    )
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_segment_content",
        new_callable=AsyncMock,
    )
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_related_segments",
        new_callable=AsyncMock,
    )
    async def test_returns_commentaries_grouped_by_text_id(
        self,
        mock_fetch_related,
        mock_fetch_content,
        mock_fetch_text,
    ):
        mock_fetch_related.return_value = _related_page(
            [
                _related_item("seg-trans-1", TRANSLATION_TEXT_ID),
                _related_item("seg-comm-1", COMMENTARY_TEXT_ID),
                _related_item("seg-comm-2", COMMENTARY_TEXT_ID),
            ]
        )

        async def content_side_effect(segment_id: str):
            return {
                PARENT_SEGMENT_ID: "Parent segment content",
                "seg-trans-1": "Translation segment 1",
                "seg-comm-1": "Commentary segment 1",
                "seg-comm-2": "Commentary segment 2",
            }.get(segment_id)

        mock_fetch_content.side_effect = content_side_effect

        async def text_side_effect(text_id: str):
            if text_id == TRANSLATION_TEXT_ID:
                return _translation_text(text_id)
            if text_id == COMMENTARY_TEXT_ID:
                return _commentary_text(text_id)
            return None

        mock_fetch_text.side_effect = text_side_effect

        result = await get_commentaries_by_segment_id_from_openpecha(
            segment_id=PARENT_SEGMENT_ID,
        )

        assert isinstance(result, V2SegmentCommentariesResponse)
        assert result.parent_segment.content == "Parent segment content"
        assert len(result.commentaries) == 1
        assert result.commentaries[0].text_id == COMMENTARY_TEXT_ID
        assert result.commentaries[0].title == f"Commentary {COMMENTARY_TEXT_ID}"
        assert result.commentaries[0].language == "bo"
        assert len(result.commentaries[0].segments) == 2
        assert result.commentaries[0].segments[0].id == "seg-comm-1"
        assert result.commentaries[0].segments[1].content == "Commentary segment 2"

    @pytest.mark.asyncio
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_text_by_id",
        new_callable=AsyncMock,
    )
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_segment_content",
        new_callable=AsyncMock,
    )
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_related_segments",
        new_callable=AsyncMock,
    )
    async def test_skips_items_when_text_lookup_fails(
        self,
        mock_fetch_related,
        mock_fetch_content,
        mock_fetch_text,
    ):
        mock_fetch_related.return_value = _related_page(
            [
                _related_item("seg-trans-1", TRANSLATION_TEXT_ID),
                _related_item("seg-unknown-1", "unknown-text"),
            ]
        )
        mock_fetch_content.return_value = "Parent content"

        async def text_side_effect(text_id: str):
            if text_id == TRANSLATION_TEXT_ID:
                return _translation_text(text_id)
            raise Exception("upstream failure")

        mock_fetch_text.side_effect = text_side_effect

        result = await get_translations_by_segment_id_from_openpecha(
            segment_id=PARENT_SEGMENT_ID,
        )

        assert len(result.translations) == 1
        assert result.translations[0].text_id == TRANSLATION_TEXT_ID
        assert len(result.translations[0].segments) == 1


class TestGetRootTextBySegmentIdFromOpenpecha:
    @pytest.mark.asyncio
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_text_by_id",
        new_callable=AsyncMock,
    )
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_segment_content",
        new_callable=AsyncMock,
    )
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_related_segments",
        new_callable=AsyncMock,
    )
    async def test_returns_root_text_segments_for_matching_text_id(
        self,
        mock_fetch_related,
        mock_fetch_content,
        mock_fetch_text,
    ):
        mock_fetch_related.return_value = _related_page(
            [
                _related_item("root-seg-1", ROOT_TEXT_ID),
                _related_item("root-seg-2", ROOT_TEXT_ID),
                _related_item("seg-trans-1", TRANSLATION_TEXT_ID),
            ],
            has_more=True,
        )

        async def content_side_effect(segment_id: str):
            return {
                PARENT_SEGMENT_ID: "Parent segment content",
                "root-seg-1": "Root segment 1",
                "root-seg-2": "Root segment 2",
            }.get(segment_id)

        mock_fetch_content.side_effect = content_side_effect
        mock_fetch_text.return_value = _root_text(ROOT_TEXT_ID)

        result = await get_root_text_by_segment_id_from_openpecha(
            text_id=ROOT_TEXT_ID,
            segment_id=PARENT_SEGMENT_ID,
            skip=0,
            limit=10,
        )

        assert isinstance(result, V2SegmentRootTextResponse)
        assert result.parent_segment.segment_id == PARENT_SEGMENT_ID
        assert result.parent_segment.content == "Parent segment content"
        assert len(result.root_text) == 1
        assert result.root_text[0].text_id == ROOT_TEXT_ID
        assert result.root_text[0].title == f"Root text {ROOT_TEXT_ID}"
        assert result.root_text[0].language == "bo"
        assert len(result.root_text[0].segments) == 2
        assert result.root_text[0].segments[0].id == "root-seg-1"
        assert result.root_text[0].segments[0].content == "Root segment 1"
        assert result.has_more is False

        mock_fetch_related.assert_awaited_once_with(
            segment_id=PARENT_SEGMENT_ID,
            limit=100,
            offset=0,
        )

    @pytest.mark.asyncio
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_text_by_id",
        new_callable=AsyncMock,
    )
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_segment_content",
        new_callable=AsyncMock,
    )
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_related_segments",
        new_callable=AsyncMock,
    )
    async def test_paginates_matching_root_text_segments(
        self,
        mock_fetch_related,
        mock_fetch_content,
        mock_fetch_text,
    ):
        async def related_side_effect(segment_id: str, limit: int, offset: int):
            if offset == 0:
                return _related_page(
                    [_related_item(f"root-seg-{index}", ROOT_TEXT_ID) for index in range(1, 3)],
                    has_more=True,
                    offset=0,
                    limit=100,
                )
            return _related_page(
                [_related_item(f"root-seg-{index}", ROOT_TEXT_ID) for index in range(3, 5)],
                has_more=False,
                offset=100,
                limit=100,
            )

        mock_fetch_related.side_effect = related_side_effect

        async def content_side_effect(segment_id: str):
            return {
                PARENT_SEGMENT_ID: "Parent segment content",
                "root-seg-1": "Root segment 1",
                "root-seg-2": "Root segment 2",
                "root-seg-3": "Root segment 3",
                "root-seg-4": "Root segment 4",
            }.get(segment_id)

        mock_fetch_content.side_effect = content_side_effect
        mock_fetch_text.return_value = _root_text(ROOT_TEXT_ID)

        result = await get_root_text_by_segment_id_from_openpecha(
            text_id=ROOT_TEXT_ID,
            segment_id=PARENT_SEGMENT_ID,
            skip=1,
            limit=2,
        )

        assert len(result.root_text) == 1
        assert len(result.root_text[0].segments) == 2
        assert result.root_text[0].segments[0].id == "root-seg-2"
        assert result.root_text[0].segments[1].id == "root-seg-3"
        assert result.skip == 1
        assert result.limit == 2
        assert result.has_more is True
        assert mock_fetch_related.await_count == 2

    @pytest.mark.asyncio
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_segment_content",
        new_callable=AsyncMock,
    )
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_related_segments",
        new_callable=AsyncMock,
    )
    async def test_returns_empty_root_text_when_no_matching_text_id(
        self,
        mock_fetch_related,
        mock_fetch_content,
    ):
        mock_fetch_related.return_value = _related_page(
            [_related_item("seg-trans-1", TRANSLATION_TEXT_ID)]
        )
        mock_fetch_content.return_value = "Parent content"

        result = await get_root_text_by_segment_id_from_openpecha(
            text_id=ROOT_TEXT_ID,
            segment_id=PARENT_SEGMENT_ID,
        )

        assert result.root_text == []
        assert result.has_more is False

    @pytest.mark.asyncio
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_segment_content",
        new_callable=AsyncMock,
    )
    @patch(
        "pecha_api.texts.segments.segments_openpecha_service.fetch_related_segments",
        new_callable=AsyncMock,
    )
    async def test_stops_fetching_after_enough_matches(
        self,
        mock_fetch_related,
        mock_fetch_content,
    ):
        mock_fetch_related.side_effect = [
            _related_page(
                [_related_item(f"root-seg-{index}", ROOT_TEXT_ID) for index in range(1, 12)],
                has_more=True,
            ),
        ]

        mock_fetch_content.return_value = "content"

        with patch(
            "pecha_api.texts.segments.segments_openpecha_service.fetch_text_by_id",
            new_callable=AsyncMock,
            return_value=_root_text(ROOT_TEXT_ID),
        ):
            result = await get_root_text_by_segment_id_from_openpecha(
                text_id=ROOT_TEXT_ID,
                segment_id=PARENT_SEGMENT_ID,
                skip=0,
                limit=10,
            )

        assert len(result.root_text[0].segments) == 10
        assert result.has_more is True
        mock_fetch_related.assert_awaited_once()
