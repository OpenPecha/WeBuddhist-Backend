from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from starlette import status

from pecha_api.cache.cache_enums import CacheType
from pecha_api.config import get as get_config
from pecha_api.error_contants import ErrorConstants
from pecha_api.recitations.recitations_response_models import (
    ListRecitationsRequest,
    RecitationCollectionDTO,
    RecitationCollectionItemType,
    RecitationDetailsRequest,
    RecitationDetailsResponse,
    RecitationDTO,
    RecitationsResponse,
    Segment,
)
from pecha_api.recitations.recitations_services import (
    _build_first_segment,
    _resolve_recitation_text_id,
    _build_recitation_segments,
    _fetch_full_edition_segments,
    _fetch_language_segment_map,
    _fetch_recitation_texts_from_openpecha,
    _get_user_collections_for_token,
    get_list_of_recitations_service,
    get_recitation_details_service,
    get_text_details_by_text_id,
)
from pecha_api.texts.text_openpecha_response_models import (
    CriticalEditionModel,
    EditionContentResponse,
    SegmentContentModel,
    SegmentationResponseModel,
    SegmentationSegmentResponseModel,
    SegmentLineModel,
    SegmentSpans,
)
from unittest.mock import AsyncMock, MagicMock, patch


class TestFetchRecitationTextsFromOpenpecha:
    """Test cases for _fetch_recitation_texts_from_openpecha."""

    @patch('pecha_api.recitations.recitations_services.fetch_texts_by_category')
    @pytest.mark.asyncio
    async def test_success(self, mock_fetch):
        mock_fetch.return_value = {
            "items": [
                {"id": "text-1", "title": {"en": "Refuge and Bodhichitta"}, "language": "en"},
                {"id": "text-2", "title": {"en": "Four Boundless Thoughts"}, "language": "en"},
            ],
            "has_more": False,
        }

        recitations, total = await _fetch_recitation_texts_from_openpecha(
            language="en", search=None, skip=0, limit=10
        )

        assert total == 2
        assert len(recitations) == 2
        assert recitations[0].text_id == "text-1"
        assert recitations[0].title == "Refuge and Bodhichitta"
        assert mock_fetch.call_args.kwargs["category_id"] == get_config("RECITATION_CATEGORY_ID")
        assert mock_fetch.call_args.kwargs["language"] == "en"

    @patch('pecha_api.recitations.recitations_services.fetch_texts_by_category')
    @pytest.mark.asyncio
    async def test_pagination_is_in_memory(self, mock_fetch):
        mock_fetch.return_value = {
            "items": [
                {"id": f"text-{i}", "title": {"en": f"Text {i}"}, "language": "en"}
                for i in range(5)
            ],
            "has_more": False,
        }

        recitations, total = await _fetch_recitation_texts_from_openpecha(
            language="en", search=None, skip=2, limit=2
        )

        assert total == 5
        assert len(recitations) == 2
        assert recitations[0].text_id == "text-2"

    @patch('pecha_api.recitations.recitations_services.fetch_texts_by_category')
    @pytest.mark.asyncio
    async def test_upstream_failure_raises_bad_gateway(self, mock_fetch):
        mock_fetch.side_effect = Exception("boom")

        with pytest.raises(HTTPException) as exc_info:
            await _fetch_recitation_texts_from_openpecha(language="en", search=None, skip=0, limit=10)

        assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY


class TestBuildFirstSegment:
    """Test cases for _build_first_segment."""

    @patch('pecha_api.recitations.recitations_services.fetch_edition_content')
    @patch('pecha_api.recitations.recitations_services.fetch_segmentation_segments')
    @patch('pecha_api.recitations.recitations_services.fetch_editions_segmentation')
    @patch('pecha_api.recitations.recitations_services.fetch_critical_editions')
    @pytest.mark.asyncio
    async def test_success(self, mock_editions, mock_segmentations, mock_segments, mock_content):
        mock_editions.return_value = [CriticalEditionModel(id="edition-1", type="critical")]
        mock_segmentations.return_value = [
            SegmentationResponseModel(id="seg-1", edition_id="edition-1", text_id="text-1")
        ]
        mock_segments.return_value = SegmentationSegmentResponseModel(
            items=[SegmentSpans(id="span-1", lines=[SegmentLineModel(start=0, end=5)])],
            has_more=False,
            offset=0,
            limit=1,
        )
        mock_content.return_value = EditionContentResponse(content="Hello world")

        result = await _build_first_segment(text_id="text-1")

        assert result is not None
        assert result.id == "span-1"
        assert result.content == "Hello"

    @patch('pecha_api.recitations.recitations_services.fetch_critical_editions')
    @pytest.mark.asyncio
    async def test_no_editions_returns_none(self, mock_editions):
        mock_editions.return_value = []

        assert await _build_first_segment(text_id="text-1") is None

    @patch('pecha_api.recitations.recitations_services.fetch_critical_editions')
    @pytest.mark.asyncio
    async def test_swallows_upstream_errors(self, mock_editions):
        mock_editions.side_effect = Exception("network error")

        assert await _build_first_segment(text_id="text-1") is None

    @patch('pecha_api.recitations.recitations_services.fetch_edition_content')
    @patch('pecha_api.recitations.recitations_services.fetch_editions_segmentation')
    @patch('pecha_api.recitations.recitations_services.fetch_critical_editions')
    @pytest.mark.asyncio
    async def test_falls_back_to_whole_content_when_no_segmentation(
        self, mock_editions, mock_segmentations, mock_content
    ):
        mock_editions.return_value = [CriticalEditionModel(id="edition-1", type="critical")]
        mock_segmentations.side_effect = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
        mock_content.return_value = EditionContentResponse(content="A" * 900)

        result = await _build_first_segment(text_id="text-1")

        assert result is not None
        assert result.id == "edition-1"
        assert len(result.content) == 500


class TestGetListOfRecitationsService:
    """Test cases for get_list_of_recitations_service."""

    @patch('pecha_api.recitations.recitations_services.set_recitation_list_cache')
    @patch('pecha_api.recitations.recitations_services.get_recitation_list_cache')
    @patch('pecha_api.recitations.recitations_services.get_recitations_with_image_urls')
    @patch('pecha_api.recitations.recitations_services._build_edition_and_first_segment')
    @patch('pecha_api.recitations.recitations_services._fetch_recitation_texts_from_openpecha')
    @pytest.mark.asyncio
    async def test_cache_miss_fetches_and_caches(
        self,
        mock_fetch_texts,
        mock_build_edition_and_first_segment,
        mock_get_images,
        mock_get_cache,
        mock_set_cache,
    ):
        mock_get_cache.return_value = None
        mock_fetch_texts.return_value = (
            [RecitationDTO(title="Refuge and Bodhichitta", text_id="text-1")],
            1,
        )
        mock_build_edition_and_first_segment.return_value = (
            "edition-1",
            Segment(id="seg-1", content="Hello"),
        )
        mock_get_images.side_effect = lambda recitations: recitations

        result = await get_list_of_recitations_service(
            request=ListRecitationsRequest(language="en")
        )

        assert isinstance(result, RecitationsResponse)
        assert len(result.recitations) == 1
        assert result.recitations[0].first_segment.content == "Hello"
        # The response carries the edition id in text_id.
        assert result.recitations[0].text_id == "edition-1"
        assert result.total == 1
        assert result.collections == []
        mock_set_cache.assert_called_once()

    @patch('pecha_api.recitations.recitations_services.set_recitation_list_cache')
    @patch('pecha_api.recitations.recitations_services.get_recitation_list_cache')
    @patch('pecha_api.recitations.recitations_services.get_recitations_with_image_urls')
    @patch('pecha_api.recitations.recitations_services._fetch_recitation_texts_from_openpecha')
    @pytest.mark.asyncio
    async def test_cache_hit_skips_upstream_fetch(
        self,
        mock_fetch_texts,
        mock_get_images,
        mock_get_cache,
        mock_set_cache,
    ):
        cached = RecitationsResponse(
            recitations=[RecitationDTO(title="Cached Title", text_id="text-1")],
            collections=[],
            skip=0,
            limit=10,
            total=1,
        )
        mock_get_cache.return_value = cached
        mock_get_images.side_effect = lambda recitations: recitations

        result = await get_list_of_recitations_service(
            request=ListRecitationsRequest(language="en")
        )

        assert result.recitations[0].title == "Cached Title"
        mock_fetch_texts.assert_not_called()
        mock_set_cache.assert_not_called()

    @patch('pecha_api.recitations.recitations_services._get_user_collections_for_token')
    @patch('pecha_api.recitations.recitations_services.set_recitation_list_cache')
    @patch('pecha_api.recitations.recitations_services.get_recitation_list_cache')
    @patch('pecha_api.recitations.recitations_services.get_recitations_with_image_urls')
    @patch('pecha_api.recitations.recitations_services._build_first_segment')
    @patch('pecha_api.recitations.recitations_services._fetch_recitation_texts_from_openpecha')
    @pytest.mark.asyncio
    async def test_includes_user_collections_with_token(
        self,
        mock_fetch_texts,
        mock_build_first_segment,
        mock_get_images,
        mock_get_cache,
        mock_set_cache,
        mock_get_user_collections,
    ):
        mock_get_cache.return_value = None
        mock_fetch_texts.return_value = ([], 0)
        mock_build_first_segment.return_value = None
        mock_get_images.side_effect = lambda recitations: recitations
        collection_id = uuid4()
        mock_get_user_collections.return_value = [
            RecitationCollectionDTO(
                type=RecitationCollectionItemType.RECITATION_COLLECTION,
                name="Morning Set",
                collection_id=collection_id,
                item_count=4,
            )
        ]

        result = await get_list_of_recitations_service(
            request=ListRecitationsRequest(
                language="en", token="valid_token", should_include_collections=True
            )
        )

        assert len(result.collections) == 1
        assert result.collections[0].name == "Morning Set"
        mock_get_user_collections.assert_called_once_with(
            token="valid_token",
            should_include_collections=True,
            should_include_group_collections=False,
        )

    def test_collection_dto_omits_group_id_for_individual(self):
        collection_id = uuid4()
        dto = RecitationCollectionDTO(
            type=RecitationCollectionItemType.RECITATION_COLLECTION,
            name="Morning Set",
            collection_id=collection_id,
            item_count=3,
        )
        data = dto.model_dump()
        assert data["type"] == RecitationCollectionItemType.RECITATION_COLLECTION
        assert "group_id" not in data
        assert data["name"] == "Morning Set"

    def test_group_collection_dto_keeps_group_id(self):
        collection_id = uuid4()
        group_id = uuid4()
        dto = RecitationCollectionDTO(
            type=RecitationCollectionItemType.GROUP_RECITATION_COLLECTION,
            name="Sangha Chants",
            collection_id=collection_id,
            group_id=group_id,
            item_count=5,
        )
        data = dto.model_dump()
        assert data["group_id"] == group_id
        assert data["item_count"] == 5


class TestGetUserCollectionsForToken:
    """Test cases for _get_user_collections_for_token."""

    @patch("pecha_api.recitations.recitations_services.validate_and_extract_user_details")
    @patch("pecha_api.recitations.recitations_services.get_group_collection_item_counts")
    @patch("pecha_api.recitations.recitations_services.get_collections_by_group_ids")
    @patch("pecha_api.recitations.recitations_services.get_joined_group_ids_by_user")
    @patch("pecha_api.recitations.recitations_services.get_following_group_ids_by_user")
    @patch("pecha_api.recitations.recitations_services.get_collection_item_counts")
    @patch("pecha_api.recitations.recitations_services.get_all_user_collections")
    @patch("pecha_api.recitations.recitations_services.SessionLocal")
    @patch("pecha_api.recitations.recitations_services._presigned_image_url")
    def test_builds_individual_and_group(
        self,
        mock_presign,
        mock_session_local,
        mock_get_collections,
        mock_item_counts,
        mock_followed_groups,
        mock_joined_groups,
        mock_group_collections,
        mock_group_item_counts,
        mock_validate,
    ):
        user_id = uuid4()
        group_id = uuid4()
        individual_id = uuid4()
        group_collection_id = uuid4()
        mock_validate.return_value = SimpleNamespace(id=user_id)
        mock_session_local.return_value.__enter__.return_value = MagicMock()
        mock_session_local.return_value.__exit__.return_value = None
        mock_get_collections.return_value = [
            SimpleNamespace(id=individual_id, name="Morning Set", img_url="collections/morning.jpg")
        ]
        mock_item_counts.return_value = {individual_id: 4}
        mock_followed_groups.return_value = [group_id]
        mock_joined_groups.return_value = []
        mock_group_collections.return_value = [
            SimpleNamespace(
                id=group_collection_id, group_id=group_id, name="Sangha Chants", img_url="group-collections/sangha.jpg"
            )
        ]
        mock_group_item_counts.return_value = {group_collection_id: 5}
        mock_presign.side_effect = [
            "https://example.com/collection.jpg",
            "https://example.com/group.jpg",
        ]

        result = _get_user_collections_for_token(
            token="valid_token",
            should_include_collections=True,
            should_include_group_collections=True,
        )

        assert len(result) == 2
        assert result[0].type == RecitationCollectionItemType.RECITATION_COLLECTION
        assert result[0].name == "Morning Set"
        assert result[0].item_count == 4
        assert result[1].type == RecitationCollectionItemType.GROUP_RECITATION_COLLECTION
        assert result[1].name == "Sangha Chants"
        assert result[1].group_id == group_id
        assert result[1].item_count == 5

    def test_without_token_returns_empty(self):
        assert _get_user_collections_for_token(
            token=None,
            should_include_collections=True,
            should_include_group_collections=True,
        ) == []

    def test_flags_false_returns_empty(self):
        assert _get_user_collections_for_token(
            token="valid_token",
            should_include_collections=False,
            should_include_group_collections=False,
        ) == []


class TestFetchFullEditionSegments:
    """Test cases for _fetch_full_edition_segments."""

    @patch('pecha_api.recitations.recitations_services.fetch_edition_content')
    @patch('pecha_api.recitations.recitations_services.fetch_segmentation_segments')
    @patch('pecha_api.recitations.recitations_services.fetch_editions_segmentation')
    @patch('pecha_api.recitations.recitations_services.fetch_critical_editions')
    @pytest.mark.asyncio
    async def test_paginates_until_exhausted(
        self, mock_editions, mock_segmentations, mock_segments, mock_content
    ):
        mock_editions.return_value = [CriticalEditionModel(id="edition-1", type="critical")]
        mock_segmentations.return_value = [
            SegmentationResponseModel(id="seg-1", edition_id="edition-1", text_id="text-1")
        ]
        page_1 = SegmentationSegmentResponseModel(
            items=[SegmentSpans(id="a", lines=[SegmentLineModel(start=0, end=1)])],
            has_more=True,
            offset=0,
            limit=1,
        )
        page_2 = SegmentationSegmentResponseModel(
            items=[SegmentSpans(id="b", lines=[SegmentLineModel(start=1, end=2)])],
            has_more=False,
            offset=1,
            limit=1,
        )
        mock_segments.side_effect = [page_1, page_2]
        mock_content.return_value = EditionContentResponse(content="XY")

        result = await _fetch_full_edition_segments(text_id="text-1")

        assert len(result) == 2
        assert result[0].content == "X"
        assert result[1].content == "Y"
        assert mock_segments.call_count == 2

    @patch('pecha_api.recitations.recitations_services.fetch_critical_editions')
    @pytest.mark.asyncio
    async def test_no_editions_returns_empty(self, mock_editions):
        mock_editions.return_value = []

        assert await _fetch_full_edition_segments(text_id="text-1") == []

    @patch('pecha_api.recitations.recitations_services.fetch_edition_content')
    @patch('pecha_api.recitations.recitations_services.fetch_editions_segmentation')
    @patch('pecha_api.recitations.recitations_services.fetch_critical_editions')
    @pytest.mark.asyncio
    async def test_falls_back_to_whole_content_when_no_segmentation(
        self, mock_editions, mock_segmentations, mock_content
    ):
        mock_editions.return_value = [CriticalEditionModel(id="edition-1", type="critical")]
        mock_segmentations.side_effect = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
        mock_content.return_value = EditionContentResponse(content="Full raw text")

        result = await _fetch_full_edition_segments(text_id="text-1")

        assert len(result) == 1
        assert result[0].id == "edition-1"
        assert result[0].content == "Full raw text"
        assert result[0].segment_number == 1

    @patch('pecha_api.recitations.recitations_services.fetch_editions_segmentation')
    @patch('pecha_api.recitations.recitations_services.fetch_critical_editions')
    @pytest.mark.asyncio
    async def test_non_404_segmentation_error_propagates(self, mock_editions, mock_segmentations):
        mock_editions.return_value = [CriticalEditionModel(id="edition-1", type="critical")]
        mock_segmentations.side_effect = HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="boom")

        with pytest.raises(HTTPException) as exc_info:
            await _fetch_full_edition_segments(text_id="text-1")

        assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY


class TestFetchLanguageSegmentMap:
    """Test cases for _fetch_language_segment_map."""

    @patch('pecha_api.recitations.recitations_services._fetch_full_edition_segments')
    @pytest.mark.asyncio
    async def test_skips_languages_without_candidate(self, mock_fetch_full):
        mock_fetch_full.return_value = [SegmentContentModel(id="a", content="A", segment_number=1)]
        candidates = [SimpleNamespace(id="text-en", language="en")]

        result = await _fetch_language_segment_map(languages=["en", "fr"], candidates=candidates)

        assert list(result.keys()) == ["en"]
        mock_fetch_full.assert_called_once_with(text_id="text-en")

    @patch('pecha_api.recitations.recitations_services._fetch_full_edition_segments')
    @pytest.mark.asyncio
    async def test_swallows_fetch_errors_per_language(self, mock_fetch_full):
        mock_fetch_full.side_effect = Exception("boom")
        candidates = [SimpleNamespace(id="text-en", language="en")]

        result = await _fetch_language_segment_map(languages=["en"], candidates=candidates)

        assert result == {"en": []}

    @pytest.mark.asyncio
    async def test_no_relevant_languages_returns_empty(self):
        candidates = [SimpleNamespace(id="text-en", language="en")]

        result = await _fetch_language_segment_map(languages=["fr"], candidates=candidates)

        assert result == {}


class TestBuildRecitationSegments:
    """Test cases for _build_recitation_segments."""

    def test_positional_alignment(self):
        language_segments = {
            "en": [
                SegmentContentModel(id="e1", content="Root 1", segment_number=1),
                SegmentContentModel(id="e2", content="Root 2", segment_number=2),
            ],
            "bo": [
                SegmentContentModel(id="b1", content="Trans 1", segment_number=1),
            ],
        }
        request = RecitationDetailsRequest(
            language="en", recitation=["en"], translations=["bo"], transliterations=[], adaptations=[]
        )

        segments = _build_recitation_segments(
            root_language="en", language_segments=language_segments, recitation_details_request=request
        )

        assert len(segments) == 2
        assert segments[0].recitation["en"].content == "Root 1"
        assert segments[0].translations["bo"].content == "Trans 1"
        assert segments[1].translations == {}

    def test_no_root_segments_returns_empty(self):
        request = RecitationDetailsRequest(
            language="en", recitation=["en"], translations=[], transliterations=[], adaptations=[]
        )

        segments = _build_recitation_segments(
            root_language="en", language_segments={}, recitation_details_request=request
        )

        assert segments == []


class TestGetRecitationDetailsService:
    """Test cases for get_recitation_details_service."""

    @pytest.fixture(autouse=True)
    def _ids_resolve_to_themselves(self):
        """These cases pass text ids; the edition lookup is covered separately."""
        with patch(
            'pecha_api.recitations.recitations_services._resolve_recitation_text_id',
            new=AsyncMock(side_effect=lambda recitation_id: recitation_id),
        ):
            yield

    @patch('pecha_api.recitations.recitations_services.get_text_details_by_text_id')
    @patch('pecha_api.recitations.recitations_services.get_recitation_by_text_id_cache')
    @pytest.mark.asyncio
    async def test_text_not_found(self, mock_get_cache, mock_get_text_details):
        mock_get_cache.return_value = None
        mock_get_text_details.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE
        )
        req = RecitationDetailsRequest(language="en", recitation=["en"], translations=[], transliterations=[], adaptations=[])

        with pytest.raises(HTTPException) as exc_info:
            await get_recitation_details_service(text_id=str(uuid4()), recitation_details_request=req)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == ErrorConstants.TEXT_NOT_FOUND_MESSAGE

    @patch('pecha_api.recitations.recitations_services.get_recitation_by_text_id_cache')
    @patch('pecha_api.recitations.recitations_services.get_text_details_by_text_id')
    @patch('pecha_api.recitations.recitations_services.get_text_versions_from_openpecha')
    @pytest.mark.asyncio
    async def test_root_text_not_found(
        self,
        mock_get_versions,
        mock_get_text_details_by_text_id,
        mock_get_cache,
    ):
        mock_get_cache.return_value = None
        main_text_id = str(uuid4())
        mock_get_text_details_by_text_id.return_value = SimpleNamespace(id=main_text_id, title="Main Title")
        mock_get_versions.return_value = MagicMock(
            text=SimpleNamespace(id="text-fr", language="fr"),
            versions=[SimpleNamespace(id="text-de", language="de")],
        )

        req = RecitationDetailsRequest(language="en", recitation=["en"], translations=[], transliterations=[], adaptations=[])
        with pytest.raises(HTTPException) as exc_info:
            await get_recitation_details_service(text_id=main_text_id, recitation_details_request=req)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == ErrorConstants.TEXT_NOT_FOUND_MESSAGE

    @patch('pecha_api.recitations.recitations_services.get_recitation_by_text_id_cache')
    @pytest.mark.asyncio
    async def test_returns_cached_data(self, mock_get_cache):
        text_id = str(uuid4())
        cached_response = RecitationDetailsResponse(text_id=text_id, title="Cached Title", segments=[])
        mock_get_cache.return_value = cached_response

        req = RecitationDetailsRequest(
            language="en", recitation=["en"], translations=[], transliterations=[], adaptations=[]
        )

        result = await get_recitation_details_service(text_id=text_id, recitation_details_request=req)

        assert result == cached_response
        assert result.text_id == text_id
        assert result.title == "Cached Title"
        mock_get_cache.assert_called_once()

    @patch('pecha_api.recitations.recitations_services.set_recitation_by_text_id_cache')
    @patch('pecha_api.recitations.recitations_services._fetch_language_segment_map')
    @patch('pecha_api.recitations.recitations_services.get_text_versions_from_openpecha')
    @patch('pecha_api.recitations.recitations_services.get_text_details_by_text_id')
    @patch('pecha_api.recitations.recitations_services.get_recitation_by_text_id_cache')
    @pytest.mark.asyncio
    async def test_success_builds_positional_segments(
        self,
        mock_get_cache,
        mock_get_text_details,
        mock_get_versions,
        mock_fetch_language_map,
        mock_set_cache,
    ):
        text_id = str(uuid4())
        mock_get_cache.return_value = None
        mock_get_text_details.return_value = SimpleNamespace(id=text_id, title="Main Title")
        mock_get_versions.return_value = MagicMock(
            text=SimpleNamespace(id="text-en", language="en"),
            versions=[SimpleNamespace(id="text-bo", language="bo")],
        )
        mock_fetch_language_map.return_value = {
            "en": [
                SegmentContentModel(id="seg-1", content="Root 1", segment_number=1),
                SegmentContentModel(id="seg-2", content="Root 2", segment_number=2),
            ],
            "bo": [
                SegmentContentModel(id="seg-1-bo", content="Trans 1", segment_number=1),
            ],
        }

        req = RecitationDetailsRequest(
            language="en", recitation=["en"], translations=["bo"], transliterations=[], adaptations=[]
        )

        result = await get_recitation_details_service(text_id=text_id, recitation_details_request=req)

        assert result.text_id == text_id
        assert result.title == "Main Title"
        assert len(result.segments) == 2
        assert result.segments[0].recitation["en"].content == "Root 1"
        assert result.segments[0].translations["bo"].content == "Trans 1"
        assert result.segments[1].translations == {}
        mock_set_cache.assert_called_once()


class TestGetTextDetailsByTextId:
    """Test cases for get_text_details_by_text_id."""

    @patch('pecha_api.recitations.recitations_services.get_text_by_id_from_openpecha')
    @pytest.mark.asyncio
    async def test_success(self, mock_get_text_detail):
        text_id = str(uuid4())
        expected_text = MagicMock(id=text_id, title="Test Text", group_id="group-123", language="en")
        mock_get_text_detail.return_value = expected_text

        result = await get_text_details_by_text_id(text_id=text_id)

        assert result == expected_text
        mock_get_text_detail.assert_called_once_with(text_id=text_id)


class TestResolveRecitationTextId:
    """The listing exposes edition ids, so details must accept either id."""

    @patch('pecha_api.recitations.recitations_services.fetch_edition_text_id')
    @pytest.mark.asyncio
    async def test_edition_id_resolves_to_its_text_id(self, mock_fetch_edition_text_id):
        mock_fetch_edition_text_id.return_value = "text-1"

        assert await _resolve_recitation_text_id(recitation_id="edition-1") == "text-1"
        mock_fetch_edition_text_id.assert_awaited_once_with(edition_id="edition-1")

    @patch('pecha_api.recitations.recitations_services.fetch_edition_text_id')
    @pytest.mark.asyncio
    async def test_unknown_edition_is_treated_as_a_text_id(self, mock_fetch_edition_text_id):
        mock_fetch_edition_text_id.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Edition with id 'text-1' not found"
        )

        assert await _resolve_recitation_text_id(recitation_id="text-1") == "text-1"

    @patch('pecha_api.recitations.recitations_services.get_recitation_by_text_id_cache')
    @patch('pecha_api.recitations.recitations_services.fetch_edition_text_id')
    @pytest.mark.asyncio
    async def test_details_service_resolves_the_edition_id_before_lookup(
        self, mock_fetch_edition_text_id, mock_get_cache
    ):
        """The region check, cache and text fetch must all key on the text id."""
        mock_fetch_edition_text_id.return_value = "text-1"
        cached_response = RecitationDetailsResponse(
            text_id="text-1", title="Cached Title", segments=[]
        )
        mock_get_cache.return_value = cached_response
        req = RecitationDetailsRequest(
            language="en", recitation=["en"], translations=[], transliterations=[], adaptations=[]
        )

        result = await get_recitation_details_service(
            text_id="edition-1", recitation_details_request=req
        )

        assert result == cached_response
        mock_fetch_edition_text_id.assert_awaited_once_with(edition_id="edition-1")
        assert mock_get_cache.await_args.kwargs["text_id"] == "text-1"

    @patch('pecha_api.recitations.recitations_services.fetch_edition_text_id')
    @pytest.mark.asyncio
    async def test_upstream_failure_is_not_swallowed(self, mock_fetch_edition_text_id):
        mock_fetch_edition_text_id.side_effect = HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="upstream"
        )

        with pytest.raises(HTTPException) as exc_info:
            await _resolve_recitation_text_id(recitation_id="edition-1")

        assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY
