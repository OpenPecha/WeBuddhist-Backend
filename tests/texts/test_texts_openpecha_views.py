from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from pecha_api.app import api
from pecha_api.collections.collections_response_models import V2CollectionModel
from pecha_api.texts.texts_response_models import V2TextDTO, V2TextsCategoryResponse

client = TestClient(api)


class TestTextsV2Endpoint:
    @patch("pecha_api.texts.texts_openpecha_views.get_texts_by_collection_from_openpecha")
    def test_get_texts_by_collection_success(self, mock_service):
        mock_service.return_value = V2TextsCategoryResponse(
            collection=V2CollectionModel(id="cat-1", title="Discourses", language="en"),
            texts=[
                V2TextDTO(id="t1", title="Text 1", language="en"),
                V2TextDTO(id="t2", title="Text 2", language="bo"),
            ],
            skip=0,
            limit=10,
        )

        response = client.get("/v2/texts/collection/cat-1?language=en")

        assert response.status_code == 200
        data = response.json()
        assert data["collection"]["title"] == "Discourses"
        assert len(data["texts"]) == 2

    @patch("pecha_api.texts.texts_openpecha_views.get_text_by_id_from_openpecha")
    def test_get_text_by_id_success(self, mock_service):
        mock_service.return_value = V2TextDTO(
            id="t1",
            title="Test Text",
            language="en",
            license="CC0",
        )

        response = client.get("/v2/texts/t1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "t1"
        assert data["title"] == "Test Text"


class TestTextsV2ValidationErrors:
    def test_invalid_skip_negative(self):
        response = client.get("/v2/texts/collection/cat-1?skip=-1")
        assert response.status_code == 422

    def test_invalid_limit_zero(self):
        response = client.get("/v2/texts/collection/cat-1?limit=0")
        assert response.status_code == 422


class TestTextsV2ErrorHandling:
    @patch("pecha_api.texts.texts_openpecha_views.get_texts_by_collection_from_openpecha")
    def test_get_texts_upstream_error(self, mock_service):
        mock_service.side_effect = HTTPException(
            status_code=502,
            detail="Failed to fetch texts from upstream service",
        )

        response = client.get("/v2/texts/collection/cat-1")

        assert response.status_code == 502
        assert "upstream" in response.json()["detail"].lower()

    @patch("pecha_api.texts.texts_openpecha_views.get_text_by_id_from_openpecha")
    def test_get_text_by_id_not_found(self, mock_service):
        mock_service.side_effect = HTTPException(
            status_code=404,
            detail="Text with id 'missing' not found",
        )

        response = client.get("/v2/texts/missing")

        assert response.status_code == 404
