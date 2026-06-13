import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from pecha_api.mantra.mantra_service import get_mantras_service, _build_mantra_dto
from pecha_api.mantra.mantra_response_models import MantraResponse, MantraDTO
from pecha_api.mantra.mantra_model import Mantra
from pecha_api.mantra.mantra_metadata_model import MantraMetadata
from pecha_api.plans.plans_enums import LanguageCode


class TestDataFactory:
    """Factory for creating test data objects."""

    @staticmethod
    def create_mock_metadata(
        metadata_id=None,
        text="Om Mani Padme Hum",
        meaning="The jewel in the lotus",
        transliteration="om mani padme hum",
        language=LanguageCode.EN,
    ):
        """Create a mock MantraMetadata entry."""
        entry = MagicMock(spec=MantraMetadata)
        entry.id = metadata_id or uuid4()
        entry.text = text
        entry.meaning = meaning
        entry.transliteration = transliteration
        entry.language = language
        return entry

    @staticmethod
    def create_mock_mantra(mantra_id=None, audio_url="audio/mantra.mp3", metadata_entries=None):
        """Create a mock Mantra model."""
        mantra = MagicMock(spec=Mantra)
        mantra.id = mantra_id or uuid4()
        mantra.audio_url = audio_url
        mantra.metadata_entries = metadata_entries or []
        return mantra


class TestGetMantrasService:
    """Test cases for get_mantras_service function."""

    @patch('pecha_api.mantra.mantra_service.SessionLocal')
    @patch('pecha_api.mantra.mantra_service.get_all_mantras')
    def test_get_mantras_service_success(self, mock_get_all, mock_session):
        """Test successful retrieval of all mantras."""
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db

        mantra1 = TestDataFactory.create_mock_mantra(
            metadata_entries=[TestDataFactory.create_mock_metadata(text="Mantra 1")]
        )
        mantra2 = TestDataFactory.create_mock_mantra(
            metadata_entries=[TestDataFactory.create_mock_metadata(text="Mantra 2")]
        )
        mock_get_all.return_value = [mantra1, mantra2]

        result = get_mantras_service()

        assert isinstance(result, MantraResponse)
        assert len(result.mantras) == 2
        assert result.mantras[0].metadata[0].text == "Mantra 1"
        mock_get_all.assert_called_once_with(mock_db, language=None)

    @patch('pecha_api.mantra.mantra_service.SessionLocal')
    @patch('pecha_api.mantra.mantra_service.get_all_mantras')
    def test_get_mantras_service_empty(self, mock_get_all, mock_session):
        """Test get_mantras_service when no mantras exist."""
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_all.return_value = []

        result = get_mantras_service()

        assert len(result.mantras) == 0

    @patch('pecha_api.mantra.mantra_service.SessionLocal')
    @patch('pecha_api.mantra.mantra_service.get_all_mantras')
    def test_get_mantras_service_passes_language_to_repository(self, mock_get_all, mock_session):
        """The language filter should be forwarded to the repository."""
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_all.return_value = []

        get_mantras_service(language="en")

        mock_get_all.assert_called_once_with(mock_db, language="en")

    @patch('pecha_api.mantra.mantra_service.SessionLocal')
    @patch('pecha_api.mantra.mantra_service.get_all_mantras')
    def test_get_mantras_service_filters_metadata_by_language(self, mock_get_all, mock_session):
        """When a language is requested, only matching metadata entries are returned."""
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db

        en_entry = TestDataFactory.create_mock_metadata(text="English", language=LanguageCode.EN)
        bo_entry = TestDataFactory.create_mock_metadata(text="Tibetan", language=LanguageCode.BO)
        mantra = TestDataFactory.create_mock_mantra(metadata_entries=[en_entry, bo_entry])
        mock_get_all.return_value = [mantra]

        result = get_mantras_service(language="en")

        assert len(result.mantras) == 1
        assert len(result.mantras[0].metadata) == 1
        assert result.mantras[0].metadata[0].language == LanguageCode.EN

    @patch('pecha_api.mantra.mantra_service.SessionLocal')
    @patch('pecha_api.mantra.mantra_service.get_all_mantras')
    def test_get_mantras_service_language_case_insensitive(self, mock_get_all, mock_session):
        """Language filtering should be case-insensitive."""
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db

        bo_entry = TestDataFactory.create_mock_metadata(text="Tibetan", language=LanguageCode.BO)
        mantra = TestDataFactory.create_mock_mantra(metadata_entries=[bo_entry])
        mock_get_all.return_value = [mantra]

        result = get_mantras_service(language="bo")

        assert len(result.mantras[0].metadata) == 1
        assert result.mantras[0].metadata[0].language == LanguageCode.BO


class TestBuildMantraDto:
    """Test cases for the _build_mantra_dto helper."""

    def test_build_mantra_dto_no_language_includes_all(self):
        """Without a language filter, all metadata entries are included."""
        entries = [
            TestDataFactory.create_mock_metadata(text="EN", language=LanguageCode.EN),
            TestDataFactory.create_mock_metadata(text="BO", language=LanguageCode.BO),
        ]
        mantra = TestDataFactory.create_mock_mantra(metadata_entries=entries)

        result = _build_mantra_dto(mantra, language=None)

        assert isinstance(result, MantraDTO)
        assert result.id == mantra.id
        assert result.audio_url == mantra.audio_url
        assert len(result.metadata) == 2

    def test_build_mantra_dto_filters_by_language(self):
        """With a language filter, only matching entries are kept."""
        entries = [
            TestDataFactory.create_mock_metadata(text="EN", language=LanguageCode.EN),
            TestDataFactory.create_mock_metadata(text="ZH", language=LanguageCode.ZH),
        ]
        mantra = TestDataFactory.create_mock_mantra(metadata_entries=entries)

        result = _build_mantra_dto(mantra, language="zh")

        assert len(result.metadata) == 1
        assert result.metadata[0].language == LanguageCode.ZH

    def test_build_mantra_dto_no_matching_language(self):
        """A language with no matching entries yields empty metadata."""
        entries = [TestDataFactory.create_mock_metadata(language=LanguageCode.EN)]
        mantra = TestDataFactory.create_mock_mantra(metadata_entries=entries)

        result = _build_mantra_dto(mantra, language="bo")

        assert len(result.metadata) == 0
