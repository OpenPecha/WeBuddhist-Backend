import pytest
from unittest.mock import patch
from uuid import uuid4

from pecha_api.mantra.mantra_views import get_mantras_endpoint
from pecha_api.mantra.mantra_response_models import MantraResponse, MantraDTO, MantraMetadataDTO
from pecha_api.plans.plans_enums import LanguageCode


class TestDataFactory:
    """Factory for creating test data objects."""

    @staticmethod
    def create_metadata_dto(text="Om Mani Padme Hum", language=LanguageCode.EN) -> MantraMetadataDTO:
        return MantraMetadataDTO(
            id=uuid4(),
            text=text,
            meaning="meaning",
            transliteration="translit",
            language=language,
        )

    @staticmethod
    def create_mantra_dto(audio_url="audio/mantra.mp3", metadata=None) -> MantraDTO:
        return MantraDTO(
            id=uuid4(),
            audio_url=audio_url,
            metadata=metadata or [TestDataFactory.create_metadata_dto()],
        )

    @staticmethod
    def create_mantra_response(mantras=None) -> MantraResponse:
        return MantraResponse(mantras=mantras or [])


class TestGetMantrasEndpoint:
    """Test cases for get_mantras_endpoint."""

    @patch('pecha_api.mantra.mantra_views.get_mantras_service')
    def test_get_mantras_endpoint_success(self, mock_service):
        """Test successful retrieval of mantras without a language filter."""
        mock_service.return_value = TestDataFactory.create_mantra_response(
            mantras=[
                TestDataFactory.create_mantra_dto(),
                TestDataFactory.create_mantra_dto(),
            ]
        )

        result = get_mantras_endpoint(language=None)

        assert isinstance(result, MantraResponse)
        assert len(result.mantras) == 2
        mock_service.assert_called_once_with(language=None)

    @patch('pecha_api.mantra.mantra_views.get_mantras_service')
    def test_get_mantras_endpoint_empty(self, mock_service):
        """Test get_mantras_endpoint when no mantras exist."""
        mock_service.return_value = TestDataFactory.create_mantra_response(mantras=[])

        result = get_mantras_endpoint(language=None)

        assert len(result.mantras) == 0

    @patch('pecha_api.mantra.mantra_views.get_mantras_service')
    def test_get_mantras_endpoint_with_language(self, mock_service):
        """Test get_mantras_endpoint forwards the language filter to the service."""
        mock_service.return_value = TestDataFactory.create_mantra_response(
            mantras=[
                TestDataFactory.create_mantra_dto(
                    metadata=[TestDataFactory.create_metadata_dto(language=LanguageCode.BO)]
                )
            ]
        )

        result = get_mantras_endpoint(language="bo")

        assert len(result.mantras) == 1
        assert result.mantras[0].metadata[0].language == LanguageCode.BO
        mock_service.assert_called_once_with(language="bo")
