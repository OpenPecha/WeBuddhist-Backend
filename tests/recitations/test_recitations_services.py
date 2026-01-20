import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4, UUID
from fastapi import HTTPException
from starlette import status

from pecha_api.recitations.recitations_services import (
    get_list_of_recitations_service,
    get_recitation_details_service,
    segments_mapping_by_toc,
    filter_by_type_and_language,
)
from pecha_api.recitations.recitations_response_models import (
    RecitationDTO,
    RecitationsResponse,
    RecitationDetailsRequest,
    RecitationDetailsResponse,
    RecitationSegment,
    Segment,
)
from pecha_api.texts.texts_response_models import TableOfContent, TableOfContentType, Section, TextSegment, TextDTO
from pecha_api.texts.segments.segments_response_models import (
    SegmentDTO,
    SegmentTranslation,
    SegmentTransliteration,
    SegmentAdaptation,
    SegmentRecitation,
)
from pecha_api.texts.segments.segments_enum import SegmentType
from pecha_api.recitations.recitations_enum import RecitationListTextType, LanguageCode
from pecha_api.texts.texts_enums import TextType
from pecha_api.error_contants import ErrorConstants
from pecha_api.cache.cache_enums import CacheType


class TestGetListOfRecitationsService:
    """Test cases for get_list_of_recitations_service function."""

    @patch('pecha_api.recitations.recitations_services.get_collection_id_by_slug')
    @patch('pecha_api.recitations.recitations_services.get_root_text_by_collection_id')
    @patch('pecha_api.recitations.recitations_services.apply_search_recitation_title_filter')
    @pytest.mark.asyncio
    async def test_get_list_of_recitations_service_success(
        self,
        mock_apply_search_filter,
        mock_get_root_text,
        mock_get_collection_id
    ):
        """Test successful retrieval of recitations list."""
        # Setup mocks
        liturgy_collection_id = str(uuid4())
        mock_get_collection_id.return_value = liturgy_collection_id
        
        text_id = str(uuid4())
        text_title = "Test Recitation"
        recitation_dto = RecitationDTO(text_id=UUID(text_id), title=text_title)
        mock_recitations_response = RecitationsResponse(recitations=[recitation_dto])
        mock_get_root_text.return_value = mock_recitations_response
        mock_apply_search_filter.return_value = [recitation_dto]
        
        # Execute
        result = await get_list_of_recitations_service(language="en")
        
        # Verify
        assert isinstance(result, RecitationsResponse)
        assert len(result.recitations) == 1
        
        recitation = result.recitations[0]
        assert isinstance(recitation, RecitationDTO)
        assert recitation.title == text_title
        assert str(recitation.text_id) == text_id
        
        # Verify mock calls
        mock_get_collection_id.assert_called_once_with(slug="Liturgy")
        mock_get_root_text.assert_called_once_with(collection_id=liturgy_collection_id, language="en")
        mock_apply_search_filter.assert_called_once_with(texts=[recitation_dto], search=None)

    @patch('pecha_api.recitations.recitations_services.get_collection_id_by_slug')
    @pytest.mark.asyncio
    async def test_get_list_of_recitations_service_collection_not_found(
        self,
        mock_get_collection_id
    ):
        """Test get_list_of_recitations_service when Liturgy collection is not found."""
        mock_get_collection_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await get_list_of_recitations_service(language="en")
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == ErrorConstants.COLLECTION_NOT_FOUND
        mock_get_collection_id.assert_called_once_with(slug="Liturgy")

    @patch('pecha_api.recitations.recitations_services.get_collection_id_by_slug')
    @patch('pecha_api.recitations.recitations_services.get_root_text_by_collection_id')
    @patch('pecha_api.recitations.recitations_services.apply_search_recitation_title_filter')
    @pytest.mark.asyncio
    async def test_get_list_of_recitations_service_search_filter_no_match(
        self,
        mock_apply_search_filter,
        mock_get_root_text,
        mock_get_collection_id
    ):
        """Test get_list_of_recitations_service when search filter returns no match."""
        liturgy_collection_id = str(uuid4())
        mock_get_collection_id.return_value = liturgy_collection_id
        
        text_id = str(uuid4())
        text_title = "Test Recitation"
        recitation_dto = RecitationDTO(text_id=UUID(text_id), title=text_title)
        mock_recitations_response = RecitationsResponse(recitations=[recitation_dto])
        mock_get_root_text.return_value = mock_recitations_response
        mock_apply_search_filter.return_value = []
        
        result = await get_list_of_recitations_service(search="nonexistent", language="en")
        
        assert isinstance(result, RecitationsResponse)
        assert len(result.recitations) == 0
        assert result.recitations == []
        
        mock_get_collection_id.assert_called_once_with(slug="Liturgy")
        mock_get_root_text.assert_called_once_with(collection_id=liturgy_collection_id, language="en")
        mock_apply_search_filter.assert_called_once_with(texts=[recitation_dto], search="nonexistent")

    @patch('pecha_api.recitations.recitations_services.get_collection_id_by_slug')
    @patch('pecha_api.recitations.recitations_services.get_root_text_by_collection_id')
    @patch('pecha_api.recitations.recitations_services.apply_search_recitation_title_filter')
    @pytest.mark.asyncio
    async def test_get_list_of_recitations_service_with_search_match(
        self,
        mock_apply_search_filter,
        mock_get_root_text,
        mock_get_collection_id
    ):
        """Test get_list_of_recitations_service when search filter matches."""
        liturgy_collection_id = str(uuid4())
        mock_get_collection_id.return_value = liturgy_collection_id
        
        text_id = str(uuid4())
        text_title = "Morning Prayer Recitation"
        recitation_dto = RecitationDTO(text_id=UUID(text_id), title=text_title)
        mock_recitations_response = RecitationsResponse(recitations=[recitation_dto])
        mock_get_root_text.return_value = mock_recitations_response
        mock_apply_search_filter.return_value = [recitation_dto]
        
        result = await get_list_of_recitations_service(search="morning", language="en")
        
        assert isinstance(result, RecitationsResponse)
        assert len(result.recitations) == 1
        assert result.recitations[0].title == text_title
        assert str(result.recitations[0].text_id) == text_id
        
        mock_get_collection_id.assert_called_once_with(slug="Liturgy")
        mock_get_root_text.assert_called_once_with(collection_id=liturgy_collection_id, language="en")
        mock_apply_search_filter.assert_called_once_with(texts=[recitation_dto], search="morning")

    @patch('pecha_api.recitations.recitations_services.get_collection_id_by_slug')
    @patch('pecha_api.recitations.recitations_services.get_root_text_by_collection_id')
    @patch('pecha_api.recitations.recitations_services.apply_search_recitation_title_filter')
    @pytest.mark.asyncio
    async def test_get_list_of_recitations_service_different_languages(
        self,
        mock_apply_search_filter,
        mock_get_root_text,
        mock_get_collection_id
    ):
        """Test get_list_of_recitations_service with different language parameters."""
        liturgy_collection_id = str(uuid4())
        mock_get_collection_id.return_value = liturgy_collection_id
        
        text_id = str(uuid4())
        text_title = "Tibetan Recitation"
        recitation_dto = RecitationDTO(text_id=UUID(text_id), title=text_title)
        mock_recitations_response = RecitationsResponse(recitations=[recitation_dto])
        mock_get_root_text.return_value = mock_recitations_response
        mock_apply_search_filter.return_value = [recitation_dto]
        
        result = await get_list_of_recitations_service(language="bo")
        
        assert isinstance(result, RecitationsResponse)
        assert len(result.recitations) == 1
        assert result.recitations[0].title == text_title
        
        # Verify language is passed correctly
        mock_get_root_text.assert_called_once_with(collection_id=liturgy_collection_id, language="bo")


class TestGetRecitationDetailsService:
    """Test cases for get_recitation_details_service function."""

   
    @patch('pecha_api.recitations.recitations_services.TextUtils.validate_text_exists')
    @patch('pecha_api.recitations.recitations_services.get_recitation_by_text_id_cache')
    @pytest.mark.asyncio
    async def test_get_recitation_details_service_text_not_found(self, mock_get_cache, mock_validate_text_exists):
        mock_validate_text_exists.return_value = False
        req = RecitationDetailsRequest(language="en", recitation=["en"], translations=[], transliterations=[], adaptations=[])
        with pytest.raises(HTTPException) as exc_info:
            await get_recitation_details_service(text_id=str(uuid4()), recitation_details_request=req)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == ErrorConstants.TEXT_NOT_FOUND_MESSAGE
        # Cache should not be checked if text doesn't exist
        mock_get_cache.assert_not_called()

    @patch('pecha_api.recitations.recitations_services.TextUtils.validate_text_exists')
    @patch('pecha_api.recitations.recitations_services.get_recitation_by_text_id_cache')
    @patch('pecha_api.recitations.recitations_services.get_text_details_by_text_id')
    @patch('pecha_api.recitations.recitations_services.get_all_texts_by_group_id')
    @patch('pecha_api.recitations.recitations_services.TextUtils.filter_text_on_root_and_version')
    @pytest.mark.asyncio
    async def test_get_recitation_details_service_root_text_not_found(
        self,
        mock_filter_texts_root_version,
        mock_get_all_texts_by_group_id,
        mock_get_text_details_by_text_id,
        mock_get_cache,
        mock_validate_text_exists,
    ):
        mock_validate_text_exists.return_value = True
        mock_get_cache.return_value = None  # No cached data
        main_text_id = str(uuid4())
        main_text = MagicMock(id=main_text_id, title="Main Title", group_id="group-1")
        mock_get_text_details_by_text_id.return_value = main_text
        mock_get_all_texts_by_group_id.return_value = [MagicMock()]
        mock_filter_texts_root_version.return_value = {TextType.ROOT_TEXT.value: None}

        req = RecitationDetailsRequest(language="en", recitation=["en"], translations=[], transliterations=[], adaptations=[])
        with pytest.raises(HTTPException) as exc_info:
            await get_recitation_details_service(text_id=main_text_id, recitation_details_request=req)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == ErrorConstants.TEXT_NOT_FOUND_MESSAGE

    @patch('pecha_api.recitations.recitations_services.TextUtils.validate_text_exists')
    @patch('pecha_api.recitations.recitations_services.get_recitation_by_text_id_cache')
    @pytest.mark.asyncio
    async def test_get_recitation_details_service_returns_cached_data(
        self,
        mock_get_cache,
        mock_validate_text_exists
    ):
        """Test that cached data is returned when available."""
        mock_validate_text_exists.return_value = True
        text_id = str(uuid4())
        
        # Create cached response
        cached_response = RecitationDetailsResponse(
            text_id=UUID(text_id),
            title="Cached Title",
            segments=[]
        )
        mock_get_cache.return_value = cached_response
        
        req = RecitationDetailsRequest(
            language="en",
            recitation=["en"],
            translations=[],
            transliterations=[],
            adaptations=[]
        )
        
        # Execute
        result = await get_recitation_details_service(text_id=text_id, recitation_details_request=req)
        
        # Verify
        assert result == cached_response
        assert result.text_id == UUID(text_id)
        assert result.title == "Cached Title"
        mock_validate_text_exists.assert_called_once_with(text_id=text_id)
        mock_get_cache.assert_called_once()


class TestSegmentsMappingByToc:
    """Test cases for _segments_mapping_by_toc function."""

    @staticmethod
    def create_mock_table_of_content(text_id: str = None, segment_ids: list = None) -> TableOfContent:
        """Create a mock TableOfContent object."""
        text_id = text_id or str(uuid4())
        segment_ids = segment_ids or [str(uuid4())]
        
        segments = [
            TextSegment(segment_id=segment_id, segment_number=i+1)
            for i, segment_id in enumerate(segment_ids)
        ]
        
        section = Section(
            id=str(uuid4()),
            title="Test Section",
            section_number=1,
            segments=segments
        )
        
        return TableOfContent(
            id=str(uuid4()),
            type=TableOfContentType.TEXT,
            text_id=text_id,
            sections=[section]
        )

    @staticmethod
    def create_mock_segment_dto(segment_id: str = None, content: str = "Test content") -> SegmentDTO:
        """Create a mock SegmentDTO object."""
        return SegmentDTO(
            id=segment_id or str(uuid4()),
            text_id=str(uuid4()),
            content=content,
            type=SegmentType.SOURCE
        )

    @staticmethod
    def create_mock_text_dto(text_id: str = None, language: str = "en") -> TextDTO:
        """Create a mock TextDTO object."""
        return TextDTO(
            id=text_id or str(uuid4()),
            title="Test Text",
            language=language,
            group_id=str(uuid4()),
            type="root",
            is_published=True,
            created_date="2023-01-01",
            updated_date="2023-01-01",
            published_date="2023-01-01",
            published_by=str(uuid4())
        )

    @staticmethod
    def create_mock_segment_translation(segment_id: str, language: str = "en", content: str = "Translation content") -> SegmentTranslation:
        """Create a mock SegmentTranslation object."""
        return SegmentTranslation(
            segment_id=segment_id,
            text_id=str(uuid4()),
            title="Translation Title",
            source="test_source",
            language=language,
            content=content
        )

    @staticmethod
    def create_mock_segment_transliteration(segment_id: str, language: str = "bo", content: str = "Transliteration content") -> SegmentTransliteration:
        """Create a mock SegmentTransliteration object."""
        return SegmentTransliteration(
            segment_id=segment_id,
            text_id=str(uuid4()),
            title="Transliteration Title",
            source="test_source",
            language=language,
            content=content
        )

    @staticmethod
    def create_mock_segment_adaptation(segment_id: str, language: str = "en", content: str = "Adaptation content") -> SegmentAdaptation:
        """Create a mock SegmentAdaptation object."""
        return SegmentAdaptation(
            segment_id=segment_id,
            text_id=str(uuid4()),
            title="Adaptation Title",
            source="test_source",
            language=language,
            content=content
        )

    @staticmethod
    def create_mock_segment_recitation(segment_id: str, language: str = "en", content: str = "Recitation content") -> SegmentRecitation:
        """Create a mock SegmentRecitation object."""
        return SegmentRecitation(
            segment_id=segment_id,
            text_id=str(uuid4()),
            title="Recitation Title",
            source="test_source",
            language=language,
            content=content
        )

    @patch('pecha_api.recitations.recitations_services.get_segment_details_by_id')
    @patch('pecha_api.recitations.recitations_services.get_related_mapped_segments')
    @patch('pecha_api.recitations.recitations_services.SegmentUtils.filter_segment_mapping_by_type_or_text_id')
    @pytest.mark.asyncio
    async def test_segments_mapping_by_toc_empty_table_of_contents(
        self,
        mock_filter_segments,
        mock_get_related_segments,
        mock_get_segment_details
    ):
        """Test mapping with empty table of contents."""
        request = RecitationDetailsRequest(
            language="en",
            recitation=["en"],
            translations=[],
            transliterations=[],
            adaptations=[]
        )

        # Execute
        result = await segments_mapping_by_toc([], request)

        # Verify
        assert len(result) == 0
        assert result == []
        
        # Verify no mock calls were made
        mock_get_segment_details.assert_not_called()
        mock_get_related_segments.assert_not_called()
        mock_filter_segments.assert_not_called()

class TestFilterByTypeAndLanguage:
    """Test cases for filter_by_type_and_language function."""

    def test_filter_by_type_and_language_translations(self):
        """Test filtering translations by language."""
        segment_id = str(uuid4())
        items = [
            SegmentTranslation(
                segment_id=segment_id,
                text_id=str(uuid4()),
                title="English Translation",
                source="test",
                language="en",
                content="English content"
            ),
            SegmentTranslation(
                segment_id=segment_id,
                text_id=str(uuid4()),
                title="Tibetan Translation",
                source="test",
                language="bo",
                content="Tibetan content"
            )
        ]
        languages = ["en"]
        
        result = filter_by_type_and_language(
            type=RecitationListTextType.TRANSLATIONS.value,
            segments=items,
            languages=languages
        )
        
        assert len(result) == 1
        assert "en" in result
        assert "bo" not in result
        assert result["en"].content == "English content"
        assert result["en"].id == UUID(segment_id)

    def test_filter_by_type_and_language_tibetan_transliteration(self):
        """Test filtering Tibetan transliterations by language."""
        segment_id = str(uuid4())
        items = [
            SegmentTransliteration(
                segment_id=segment_id,
                text_id=str(uuid4()),
                title="Tibetan Transliteration",
                source="test",
                language="bo",
                content="Original Tibetan content"
            )
        ]
        languages = ["bo"]
        
        result = filter_by_type_and_language(
            type=RecitationListTextType.TRANSLITERATIONS.value,
            segments=items,
            languages=languages
        )
        
        assert len(result) == 1
        assert "bo" in result
        assert result["bo"].content == "Original Tibetan content"
        assert result["bo"].id == UUID(segment_id)

    def test_filter_by_type_and_language_non_tibetan_transliteration(self):
        """Test filtering transliterations for non-Tibetan languages."""
        segment_id = str(uuid4())
        items = [
            SegmentTransliteration(
                segment_id=segment_id,
                text_id=str(uuid4()),
                title="English Transliteration",
                source="test",
                language="en",
                content="English transliteration content"
            )
        ]
        languages = ["en"]
        
        result = filter_by_type_and_language(
            type=RecitationListTextType.TRANSLITERATIONS.value,
            segments=items,
            languages=languages
        )
        
        assert len(result) == 1
        assert "en" in result
        assert result["en"].content == "English transliteration content"
        assert result["en"].id == UUID(segment_id)

    def test_filter_by_type_and_language_empty_items(self):
        """Test filtering with empty items list."""
        result = filter_by_type_and_language(
            type=RecitationListTextType.TRANSLATIONS.value,
            segments=[],
            languages=["en"]
        )
        
        assert len(result) == 0
        assert result == {}

    def test_filter_by_type_and_language_no_matching_languages(self):
        """Test filtering when no items match requested languages."""
        segment_id = str(uuid4())
        items = [
            SegmentTranslation(
                segment_id=segment_id,
                text_id=str(uuid4()),
                title="French Translation",
                source="test",
                language="fr",
                content="French content"
            )
        ]
        languages = ["en", "bo"]  # Request different languages
        
        result = filter_by_type_and_language(
            type=RecitationListTextType.TRANSLATIONS.value,
            segments=items,
            languages=languages
        )
        
        assert len(result) == 0
        assert result == {}

    def test_filter_by_type_and_language_recitations(self):
        """Test filtering recitations by language."""
        segment_id = str(uuid4())
        items = [
            SegmentRecitation(
                segment_id=segment_id,
                text_id=str(uuid4()),
                title="English Recitation",
                source="test",
                language="en",
                content="English recitation content"
            ),
            SegmentRecitation(
                segment_id=segment_id,
                text_id=str(uuid4()),
                title="Tibetan Recitation",
                source="test",
                language="bo",
                content="Tibetan recitation content"
            )
        ]
        languages = ["en"]
        
        result = filter_by_type_and_language(
            type=RecitationListTextType.RECITATIONS.value,
            segments=items,
            languages=languages
        )
        
        assert len(result) == 1
        assert "en" in result
        assert "bo" not in result
        assert result["en"].content == "English recitation content"
        assert result["en"].id == UUID(segment_id)

    def test_filter_by_type_and_language_adaptations(self):
        """Test filtering adaptations by language."""
        segment_id = str(uuid4())
        items = [
            SegmentAdaptation(
                segment_id=segment_id,
                text_id=str(uuid4()),
                title="English Adaptation",
                source="test",
                language="en",
                content="English adaptation content"
            )
        ]
        languages = ["en", "bo"]
        
        result = filter_by_type_and_language(
            type=RecitationListTextType.ADAPTATIONS.value,
            segments=items,
            languages=languages
        )
        
        assert len(result) == 1
        assert "en" in result
        assert result["en"].content == "English adaptation content"
        assert result["en"].id == UUID(segment_id)


class TestGetTextDetailsByTextId:
    """Test cases for get_text_details_by_text_id function."""

    @patch('pecha_api.recitations.recitations_services.TextUtils.get_text_detail_by_id')
    @pytest.mark.asyncio
    async def test_get_text_details_by_text_id_success(self, mock_get_text_detail):
        """Test successful retrieval of text details by text_id."""
        from pecha_api.recitations.recitations_services import get_text_details_by_text_id
        
        text_id = str(uuid4())
        expected_text = MagicMock(
            id=text_id,
            title="Test Text",
            group_id="group-123",
            language="en"
        )
        mock_get_text_detail.return_value = expected_text
        
        result = await get_text_details_by_text_id(text_id=text_id)
        
        assert result == expected_text
        mock_get_text_detail.assert_called_once_with(text_id=text_id)


class TestGetRecitationDetailsServiceSuccess:
    """Test cases for successful get_recitation_details_service execution."""

    @patch('pecha_api.recitations.recitations_services.TextUtils.validate_text_exists')
    @patch('pecha_api.recitations.recitations_services.get_recitation_by_text_id_cache')
    @patch('pecha_api.recitations.recitations_services.get_text_details_by_text_id')
    @patch('pecha_api.recitations.recitations_services.get_all_texts_by_group_id')
    @patch('pecha_api.recitations.recitations_services.TextUtils.filter_text_on_root_and_version')
    @patch('pecha_api.recitations.recitations_services.get_contents_by_id')
    @patch('pecha_api.recitations.recitations_services.segments_mapping_by_toc')
    @patch('pecha_api.recitations.recitations_services.set_recitation_by_text_id_cache')
    @pytest.mark.asyncio
    async def test_get_recitation_details_service_success(
        self,
        mock_set_cache,
        mock_segments_mapping,
        mock_get_contents,
        mock_filter_texts,
        mock_get_all_texts,
        mock_get_text_details,
        mock_get_cache,
        mock_validate_text,
    ):
        """Test successful execution of get_recitation_details_service."""
        # Setup
        text_id = str(uuid4())
        group_id = str(uuid4())
        root_text_id = str(uuid4())
        
        mock_validate_text.return_value = True
        mock_get_cache.return_value = None  # No cached data
        
        main_text = TextDTO(
            id=text_id,
            title="Main Text Title",
            group_id=group_id,
            language="en",
            type="root_text",
            is_published=True,
            created_date="2023-01-01",
            updated_date="2023-01-01",
            published_date="2023-01-01",
            published_by=str(uuid4())
        )
        mock_get_text_details.return_value = main_text
        
        texts = [main_text]
        mock_get_all_texts.return_value = texts
        
        root_text = TextDTO(
            id=root_text_id,
            title="Root Text Title",
            group_id=group_id,
            language="en",
            type="root_text",
            is_published=True,
            created_date="2023-01-01",
            updated_date="2023-01-01",
            published_date="2023-01-01",
            published_by=str(uuid4())
        )
        mock_filter_texts.return_value = {TextType.ROOT_TEXT.value: root_text}
        
        toc = [TableOfContent(id=str(uuid4()), type=TableOfContentType.TEXT, text_id=root_text_id, sections=[])]
        mock_get_contents.return_value = toc
        
        mock_segments = [RecitationSegment()]
        mock_segments_mapping.return_value = mock_segments
        
        request = RecitationDetailsRequest(
            language="en",
            recitation=["en"],
            translations=[],
            transliterations=[],
            adaptations=[]
        )
        
        # Execute
        result = await get_recitation_details_service(text_id=text_id, recitation_details_request=request)
        
        # Verify
        assert result.text_id == UUID(text_id)
        assert result.title == "Main Text Title"
        assert result.segments == mock_segments
        
        mock_validate_text.assert_called_once_with(text_id=text_id)
        mock_get_cache.assert_called_once()
        mock_get_text_details.assert_called_once_with(text_id=text_id)
        mock_get_all_texts.assert_called_once_with(group_id=group_id)
        mock_filter_texts.assert_called_once()
        mock_get_contents.assert_called_once_with(text_id=root_text_id)
        mock_segments_mapping.assert_called_once_with(table_of_contents=toc, recitation_details_request=request)
        
        # Verify cache was set
        mock_set_cache.assert_called_once()
        call_args = mock_set_cache.call_args
        assert call_args.kwargs['text_id'] == text_id
        assert call_args.kwargs['recitation_details_request'] == request
        assert call_args.kwargs['data'] == result


class TestSegmentsMappingByTocWithData:
    """Test cases for segments_mapping_by_toc with actual data."""

    @patch('pecha_api.recitations.recitations_services.get_segment_details_by_id')
    @patch('pecha_api.recitations.recitations_services.get_related_mapped_segments')
    @patch('pecha_api.recitations.recitations_services.SegmentUtils.filter_segment_mapping_by_type_or_text_id')
    @pytest.mark.asyncio
    async def test_segments_mapping_by_toc_with_single_segment(
        self,
        mock_filter_segments,
        mock_get_related_segments,
        mock_get_segment_details
    ):
        """Test segments_mapping_by_toc with a single segment."""
        segment_id = str(uuid4())
        text_id = str(uuid4())
        
        # Create table of content with one segment
        toc = [
            TableOfContent(
                id=str(uuid4()),
                type=TableOfContentType.TEXT,
                text_id=text_id,
                sections=[
                    Section(
                        id=str(uuid4()),
                        title="Section 1",
                        section_number=1,
                        segments=[
                            TextSegment(segment_id=segment_id, segment_number=1)
                        ]
                    )
                ]
            )
        ]
        
        # Mock segment details
        segment_dto = SegmentDTO(
            id=segment_id,
            text_id=text_id,
            content="Test segment content",
            type=SegmentType.SOURCE
        )
        mock_get_segment_details.return_value = segment_dto
        mock_get_related_segments.return_value = []
        
        # Mock filter responses for each type
        mock_filter_segments.return_value = []
        
        request = RecitationDetailsRequest(
            language="en",
            recitation=["en"],
            translations=["en"],
            transliterations=["bo"],
            adaptations=["en"]
        )
        
        # Execute
        result = await segments_mapping_by_toc(table_of_contents=toc, recitation_details_request=request)
        
        # Verify
        assert len(result) == 1
        assert isinstance(result[0], RecitationSegment)
        
        # Verify segment details were fetched
        mock_get_segment_details.assert_called_once_with(segment_id=segment_id, text_details=True)
        mock_get_related_segments.assert_called_once_with(parent_segment_id=segment_id)
        
        # Verify filter was called 4 times (recitations, translations, transliterations, adaptations)
        assert mock_filter_segments.call_count == 4

    @patch('pecha_api.recitations.recitations_services.get_segment_details_by_id')
    @patch('pecha_api.recitations.recitations_services.get_related_mapped_segments')
    @patch('pecha_api.recitations.recitations_services.SegmentUtils.filter_segment_mapping_by_type_or_text_id')
    @pytest.mark.asyncio
    async def test_segments_mapping_by_toc_with_multiple_segments(
        self,
        mock_filter_segments,
        mock_get_related_segments,
        mock_get_segment_details
    ):
        """Test segments_mapping_by_toc with multiple segments."""
        segment_id_1 = str(uuid4())
        segment_id_2 = str(uuid4())
        text_id = str(uuid4())
        
        # Create table of content with two segments
        toc = [
            TableOfContent(
                id=str(uuid4()),
                type=TableOfContentType.TEXT,
                text_id=text_id,
                sections=[
                    Section(
                        id=str(uuid4()),
                        title="Section 1",
                        section_number=1,
                        segments=[
                            TextSegment(segment_id=segment_id_1, segment_number=1),
                            TextSegment(segment_id=segment_id_2, segment_number=2)
                        ]
                    )
                ]
            )
        ]
        
        # Mock segment details
        def get_segment_side_effect(segment_id, text_details):
            return SegmentDTO(
                id=segment_id,
                text_id=text_id,
                content=f"Content for {segment_id}",
                type=SegmentType.SOURCE
            )
        
        mock_get_segment_details.side_effect = get_segment_side_effect
        mock_get_related_segments.return_value = []
        mock_filter_segments.return_value = []
        
        request = RecitationDetailsRequest(
            language="en",
            recitation=["en"],
            translations=[],
            transliterations=[],
            adaptations=[]
        )
        
        # Execute
        result = await segments_mapping_by_toc(table_of_contents=toc, recitation_details_request=request)
        
        # Verify
        assert len(result) == 2
        assert all(isinstance(seg, RecitationSegment) for seg in result)
        
        # Verify segment details were fetched for both segments
        assert mock_get_segment_details.call_count == 2
        assert mock_get_related_segments.call_count == 2

    @patch('pecha_api.recitations.recitations_services.get_segment_details_by_id')
    @patch('pecha_api.recitations.recitations_services.get_related_mapped_segments')
    @patch('pecha_api.recitations.recitations_services.SegmentUtils.filter_segment_mapping_by_type_or_text_id')
    @pytest.mark.asyncio
    async def test_segments_mapping_by_toc_with_filtered_data(
        self,
        mock_filter_segments,
        mock_get_related_segments,
        mock_get_segment_details
    ):
        """Test segments_mapping_by_toc with filtered segment data."""
        segment_id = str(uuid4())
        text_id = str(uuid4())
        
        toc = [
            TableOfContent(
                id=str(uuid4()),
                type=TableOfContentType.TEXT,
                text_id=text_id,
                sections=[
                    Section(
                        id=str(uuid4()),
                        title="Section 1",
                        section_number=1,
                        segments=[
                            TextSegment(segment_id=segment_id, segment_number=1)
                        ]
                    )
                ]
            )
        ]
        
        segment_dto = SegmentDTO(
            id=segment_id,
            text_id=text_id,
            content="Test content",
            type=SegmentType.SOURCE
        )
        mock_get_segment_details.return_value = segment_dto
        
        # Mock some related segments
        related_segment = SegmentDTO(
            id=str(uuid4()),
            text_id=str(uuid4()),
            content="Related content",
            type=SegmentType.SOURCE
        )
        mock_get_related_segments.return_value = [related_segment]
        
        # Mock filter to return actual segments
        mock_translation = SegmentTranslation(
            segment_id=str(uuid4()),
            text_id=str(uuid4()),
            title="Translation",
            source="test",
            language="en",
            content="Translated content"
        )
        
        def filter_side_effect(segments, type):
            if type == TextType.VERSION.value:
                return [mock_translation]
            return []
        
        mock_filter_segments.side_effect = filter_side_effect
        
        request = RecitationDetailsRequest(
            language="en",
            recitation=["en"],
            translations=["en"],
            transliterations=[],
            adaptations=[]
        )
        
        # Execute
        result = await segments_mapping_by_toc(table_of_contents=toc, recitation_details_request=request)
        
        # Verify
        assert len(result) == 1
        recitation_segment = result[0]
        assert isinstance(recitation_segment, RecitationSegment)
        
        # Verify that related segments were retrieved
        mock_get_related_segments.assert_called_once_with(parent_segment_id=segment_id)

    @patch('pecha_api.recitations.recitations_services.get_segment_details_by_id')
    @patch('pecha_api.recitations.recitations_services.get_related_mapped_segments')
    @patch('pecha_api.recitations.recitations_services.SegmentUtils.filter_segment_mapping_by_type_or_text_id')
    @patch('pecha_api.recitations.recitations_services.filter_by_type_and_language')
    @pytest.mark.asyncio
    async def test_segments_mapping_by_toc_calls_filter_by_type_and_language(
        self,
        mock_filter_by_type_lang,
        mock_filter_segments,
        mock_get_related_segments,
        mock_get_segment_details
    ):
        """Test that segments_mapping_by_toc properly calls filter_by_type_and_language for all segment types."""
        segment_id = str(uuid4())
        text_id = str(uuid4())
        
        toc = [
            TableOfContent(
                id=str(uuid4()),
                type=TableOfContentType.TEXT,
                text_id=text_id,
                sections=[
                    Section(
                        id=str(uuid4()),
                        title="Section 1",
                        section_number=1,
                        segments=[
                            TextSegment(segment_id=segment_id, segment_number=1)
                        ]
                    )
                ]
            )
        ]
        
        segment_dto = SegmentDTO(
            id=segment_id,
            text_id=text_id,
            content="Test content",
            type=SegmentType.SOURCE
        )
        mock_get_segment_details.return_value = segment_dto
        mock_get_related_segments.return_value = []
        
        # Mock filter to return mock segments
        mock_recitation = SegmentTranslation(
            segment_id=str(uuid4()),
            text_id=str(uuid4()),
            title="Recitation",
            source="test",
            language="en",
            content="Recitation content"
        )
        mock_translation = SegmentTranslation(
            segment_id=str(uuid4()),
            text_id=str(uuid4()),
            title="Translation",
            source="test",
            language="bo",
            content="Translation content"
        )
        
        mock_filter_segments.return_value = [mock_recitation, mock_translation]
        
        # Mock filter_by_type_and_language to return empty dicts
        mock_filter_by_type_lang.return_value = {}
        
        request = RecitationDetailsRequest(
            language="en",
            recitation=["en"],
            translations=["bo"],
            transliterations=["bo"],
            adaptations=["en"]
        )
        
        # Execute
        result = await segments_mapping_by_toc(table_of_contents=toc, recitation_details_request=request)
        
        # Verify
        assert len(result) == 1
        
        # Verify filter_by_type_and_language was called 4 times (once for each type)
        assert mock_filter_by_type_lang.call_count == 4
        
        # Verify the calls were made with correct types
        call_types = [call.kwargs['type'] for call in mock_filter_by_type_lang.call_args_list]
        assert RecitationListTextType.RECITATIONS.value in call_types
        assert RecitationListTextType.TRANSLATIONS.value in call_types
        assert RecitationListTextType.TRANSLITERATIONS.value in call_types
        assert RecitationListTextType.ADAPTATIONS.value in call_types