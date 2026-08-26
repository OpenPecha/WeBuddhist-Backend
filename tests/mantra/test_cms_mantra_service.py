import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException

from pecha_api.mantra.mantra_response_models import CreateMantraRequest, MantraMetadataInput
from pecha_api.mantra.mantra_service import create_mantra_service
from pecha_api.plans.plans_enums import LanguageCode


class TestCreateMantraService:
    @patch("pecha_api.mantra.mantra_service.validate_cms_author_details")
    @patch("pecha_api.mantra.mantra_service.SessionLocal")
    @patch("pecha_api.mantra.mantra_service.save_mantra")
    @patch("pecha_api.mantra.mantra_service._build_mantra_dto")
    def test_create_mantra_service_success(
        self,
        mock_build_dto,
        mock_save_mantra,
        mock_session,
        mock_validate_auth,
    ):
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db

        saved_mantra = MagicMock()
        mock_save_mantra.return_value = saved_mantra
        expected_dto = MagicMock()
        mock_build_dto.return_value = expected_dto

        request = CreateMantraRequest(
            audio_url="mantras/test.mp3",
            metadata=[
                MantraMetadataInput(
                    mantra="Om mani padme hum",
                    title="Compassion mantra",
                    language=LanguageCode.EN,
                )
            ],
        )

        result = create_mantra_service(token="token", request=request)

        assert result is expected_dto
        mock_validate_auth.assert_called_once_with(token="token")
        mock_save_mantra.assert_called_once()
        mock_build_dto.assert_called_once_with(saved_mantra, language=None)

    @patch("pecha_api.mantra.mantra_service.validate_cms_author_details")
    @patch("pecha_api.mantra.mantra_service.SessionLocal")
    @patch("pecha_api.mantra.mantra_service.get_mala_image_by_id")
    def test_create_mantra_service_invalid_mala_image(
        self,
        mock_get_mala,
        mock_session,
        mock_validate_auth,
    ):
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_mala.return_value = None

        mala_id = uuid4()
        request = CreateMantraRequest(
            mala_image_id=mala_id,
            metadata=[
                MantraMetadataInput(
                    mantra="Om mani padme hum",
                    language=LanguageCode.EN,
                )
            ],
        )

        with pytest.raises(HTTPException) as exc_info:
            create_mantra_service(token="token", request=request)

        assert exc_info.value.status_code == 400
        assert str(mala_id) in exc_info.value.detail
