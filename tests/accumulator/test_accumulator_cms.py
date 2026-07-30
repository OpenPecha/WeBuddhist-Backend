from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from pecha_api.app import api
from pecha_api.accumulator.accumulator_enums import AccumulatorType
from pecha_api.accumulator.accumulator_response_models import (
    AccumulatorMetadataDTO,
    CreatePresetAccumulatorRequest,
    UpdatePresetAccumulatorRequest,
    PublicAccumulatorDTO,
    PublicAccumulatorsResponse,
)
from pecha_api.accumulator.accumulator_cms_service import (
    create_preset_accumulator_cms_service,
    update_preset_accumulator_cms_service,
    delete_preset_accumulator_cms_service,
    get_preset_accumulator_cms_service,
    list_preset_accumulators_cms_service,
)
from pecha_api.plans.plans_enums import LanguageCode

client = TestClient(api)


def _sample_public_dto(**overrides) -> PublicAccumulatorDTO:
    data = {
        "id": uuid4(),
        "group_id": None,
        "type": AccumulatorType.PRESET,
        "target_count": 100000,
        "current_count": 0,
        "text_id": uuid4(),
        "mantra": None,
        "mala_image_id": None,
        "mala_image_url": None,
        "metadata": [
            AccumulatorMetadataDTO(
                language=LanguageCode.EN,
                name="Chenrezig Practice",
                description="Compassion practice",
            )
        ],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": None,
    }
    data.update(overrides)
    return PublicAccumulatorDTO(**data)


class TestCmsPresetViews:
    @patch("pecha_api.accumulator.accumulator_cms_views.create_preset_accumulator_cms_service")
    def test_create_preset_success(self, mock_service):
        sample = _sample_public_dto()
        mock_service.return_value = sample
        payload = {
            "target_count": 100000,
            "text_id": str(sample.text_id),
            "mantra_id": str(uuid4()),
            "metadata": [
                {"language": "EN", "name": "Chenrezig Practice", "description": "Compassion practice"}
            ],
        }

        response = client.post(
            "/api/v1/cms/accumulators/presets",
            json=payload,
            headers={"Authorization": "Bearer dummy"},
        )

        assert response.status_code == 201
        assert response.json()["id"] == str(sample.id)
        mock_service.assert_called_once()

    def test_create_preset_requires_auth(self):
        response = client.post(
            "/api/v1/cms/accumulators/presets",
            json={
                "metadata": [{"language": "EN", "name": "Test"}],
            },
        )
        assert response.status_code == 403

    def test_create_preset_rejects_empty_metadata(self):
        response = client.post(
            "/api/v1/cms/accumulators/presets",
            json={"metadata": []},
            headers={"Authorization": "Bearer dummy"},
        )
        assert response.status_code == 422

    @patch("pecha_api.accumulator.accumulator_cms_views.list_preset_accumulators_cms_service")
    def test_list_presets_success(self, mock_service):
        sample = _sample_public_dto()
        mock_service.return_value = PublicAccumulatorsResponse(
            accumulators=[sample],
            total=1,
            skip=0,
            limit=20,
        )

        response = client.get(
            "/api/v1/cms/accumulators/presets?search=chen",
            headers={"Authorization": "Bearer dummy"},
        )

        assert response.status_code == 200
        assert response.json()["total"] == 1
        mock_service.assert_called_once()

    @patch("pecha_api.accumulator.accumulator_cms_views.get_preset_accumulator_cms_service")
    def test_get_preset_success(self, mock_service):
        sample = _sample_public_dto()
        mock_service.return_value = sample

        response = client.get(
            f"/api/v1/cms/accumulators/presets/{sample.id}",
            headers={"Authorization": "Bearer dummy"},
        )

        assert response.status_code == 200
        assert response.json()["id"] == str(sample.id)

    @patch("pecha_api.accumulator.accumulator_cms_views.update_preset_accumulator_cms_service")
    def test_update_preset_success(self, mock_service):
        sample = _sample_public_dto(target_count=200000)
        mock_service.return_value = sample

        response = client.put(
            f"/api/v1/cms/accumulators/presets/{sample.id}",
            json={"target_count": 200000},
            headers={"Authorization": "Bearer dummy"},
        )

        assert response.status_code == 200
        assert response.json()["target_count"] == 200000

    @patch("pecha_api.accumulator.accumulator_cms_views.delete_preset_accumulator_cms_service")
    def test_delete_preset_success(self, mock_service):
        preset_id = uuid4()
        mock_service.return_value = None

        response = client.delete(
            f"/api/v1/cms/accumulators/presets/{preset_id}",
            headers={"Authorization": "Bearer dummy"},
        )

        assert response.status_code == 204
        mock_service.assert_called_once()


class TestCmsPresetService:
    @pytest.mark.asyncio
    @patch("pecha_api.accumulator.accumulator_cms_service.validate_cms_author_details")
    @patch("pecha_api.accumulator.accumulator_cms_service.SessionLocal")
    @patch("pecha_api.accumulator.accumulator_cms_service.TextUtils.validate_text_exists", new_callable=AsyncMock)
    @patch("pecha_api.accumulator.accumulator_cms_service.validate_mantra_exists")
    @patch("pecha_api.accumulator.accumulator_cms_service.save_accumulator")
    @patch("pecha_api.accumulator.accumulator_cms_service._to_public_dto")
    async def test_create_preset_service_success(
        self,
        mock_to_dto,
        mock_save,
        mock_validate_mantra,
        mock_validate_text,
        mock_session,
        mock_validate_auth,
    ):
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        saved = MagicMock()
        mock_save.return_value = saved
        expected = _sample_public_dto()
        mock_to_dto.return_value = expected

        text_id = uuid4()
        mantra_id = uuid4()
        request = CreatePresetAccumulatorRequest(
            target_count=108000,
            text_id=text_id,
            mantra_id=mantra_id,
            metadata=[
                AccumulatorMetadataDTO(
                    language=LanguageCode.EN,
                    name="Mani Practice",
                )
            ],
        )

        result = await create_preset_accumulator_cms_service(token="token", request=request)

        assert result is expected
        mock_validate_auth.assert_called_once_with(token="token")
        mock_validate_text.assert_awaited_once_with(text_id=str(text_id))
        mock_validate_mantra.assert_called_once_with(mock_db, mantra_id)
        mock_save.assert_called_once()

    @pytest.mark.asyncio
    @patch("pecha_api.accumulator.accumulator_cms_service.validate_cms_author_details")
    @patch("pecha_api.accumulator.accumulator_cms_service.SessionLocal")
    @patch("pecha_api.accumulator.accumulator_cms_service.get_preset_by_id")
    async def test_update_preset_not_found(
        self,
        mock_get_preset,
        mock_session,
        mock_validate_auth,
    ):
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_preset.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await update_preset_accumulator_cms_service(
                token="token",
                preset_id=uuid4(),
                request=UpdatePresetAccumulatorRequest(target_count=1),
            )

        assert exc_info.value.status_code == 404

    @patch("pecha_api.accumulator.accumulator_cms_service.validate_cms_author_details")
    @patch("pecha_api.accumulator.accumulator_cms_service.SessionLocal")
    @patch("pecha_api.accumulator.accumulator_cms_service.get_preset_by_id")
    @patch("pecha_api.accumulator.accumulator_cms_service.delete_accumulator")
    def test_delete_preset_service_success(
        self,
        mock_delete,
        mock_get_preset,
        mock_session,
        mock_validate_auth,
    ):
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        preset = MagicMock()
        preset.type = AccumulatorType.PRESET
        mock_get_preset.return_value = preset

        delete_preset_accumulator_cms_service(token="token", preset_id=uuid4())

        mock_delete.assert_called_once_with(mock_db, preset)

    @patch("pecha_api.accumulator.accumulator_cms_service.validate_cms_author_details")
    @patch("pecha_api.accumulator.accumulator_cms_service.SessionLocal")
    @patch("pecha_api.accumulator.accumulator_cms_service.get_preset_by_id")
    def test_get_preset_service_not_found(
        self,
        mock_get_preset,
        mock_session,
        mock_validate_auth,
    ):
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_preset.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_preset_accumulator_cms_service(token="token", preset_id=uuid4())

        assert exc_info.value.status_code == 404

    @patch("pecha_api.accumulator.accumulator_cms_service.validate_cms_author_details")
    @patch("pecha_api.accumulator.accumulator_cms_service.SessionLocal")
    @patch("pecha_api.accumulator.accumulator_cms_service.get_all_accumulators")
    @patch("pecha_api.accumulator.accumulator_cms_service.get_mantras_by_ids")
    def test_list_presets_service_success(
        self,
        mock_get_mantras,
        mock_get_all,
        mock_session,
        mock_validate_auth,
    ):
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_all.return_value = ([], 0)
        mock_get_mantras.return_value = {}

        result = list_preset_accumulators_cms_service(token="token", skip=0, limit=20)

        assert result.total == 0
        assert result.accumulators == []
        mock_validate_auth.assert_called_once_with(token="token")
