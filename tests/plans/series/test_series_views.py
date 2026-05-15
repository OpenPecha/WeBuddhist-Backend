import uuid
import pytest
from unittest.mock import patch, MagicMock

from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette import status

from pecha_api.app import api
from pecha_api.plans.plans_enums import PlanStatus, LanguageCode, DifficultyLevel
from pecha_api.plans.series.service_response_models import SeriesDTO, SeriesListResponse, SeriesPlanDTO


client = TestClient(api)


@pytest.fixture
def sample_series_dto():
    return SeriesDTO(
        id=uuid.uuid4(),
        name={"en": "Foundations of Meditation", "bo": "སྒོམ་"},
        image="https://example.com/presigned/series.jpg",
        image_key="series/cover.jpg",
        author_id=uuid.uuid4(),
        featured=True,
        status=PlanStatus.DRAFT,
        total_days=0,
    )


@pytest.fixture
def sample_series_list_response(sample_series_dto):
    return SeriesListResponse(
        series=[sample_series_dto],
        skip=0,
        limit=10,
        total=1,
    )


def test_get_series_list_success(sample_series_list_response):
    with patch(
        "pecha_api.plans.series.public_series_view.get_filtered_series",
        return_value=sample_series_list_response,
    ) as mock_service:
        response = client.get("/series")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        mock_service.assert_called_once_with(search=None, skip=0, limit=10)

        assert "series" in data
        assert data["skip"] == 0
        assert data["limit"] == 10
        assert data["total"] == 1
        assert len(data["series"]) == 1

        item = data["series"][0]
        assert item["name"] == sample_series_list_response.series[0].name
        assert item["author_id"] == str(sample_series_list_response.series[0].author_id)
        assert item["featured"] is True
        assert item["status"] == PlanStatus.DRAFT.value
        assert item["image"] == sample_series_list_response.series[0].image
        assert item["image_key"] == sample_series_list_response.series[0].image_key


def test_get_series_list_with_search_pagination(sample_series_dto):
    empty_list = SeriesListResponse(series=[], skip=2, limit=5, total=0)
    with patch(
        "pecha_api.plans.series.public_series_view.get_filtered_series",
        return_value=empty_list,
    ) as mock_service:
        response = client.get("/series", params={"search": "meditation", "skip": 2, "limit": 5})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        mock_service.assert_called_once_with(search="meditation", skip=2, limit=5)

        assert data["series"] == []
        assert data["skip"] == 2
        assert data["limit"] == 5
        assert data["total"] == 0


def test_create_series_success(sample_series_dto):
    author_id = uuid.uuid4()
    payload = {
        "name": {"en": "New Series"},
        "image_key": "series/uploads/key.jpg",
        "featured": False,
    }

    mock_author = MagicMock()
    mock_author.id = author_id

    with patch(
        "pecha_api.plans.series.series_view.create_new_series",
        return_value=sample_series_dto,
    ) as mock_create, patch(
        "pecha_api.plans.series.series_service.validate_and_extract_author_details",
        return_value=mock_author,
    ):
        response = client.post(
            "/cms/series",
            json=payload,
            headers={"Authorization": "Bearer dummy"}
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["token"] == "dummy"
        assert call_kwargs["create_series_request"].name == payload["name"]
        assert call_kwargs["create_series_request"].image_key == payload["image_key"]
        assert call_kwargs["create_series_request"].featured is False

        assert data["id"] == str(sample_series_dto.id)  
        assert data["name"] == sample_series_dto.name
        assert data["status"] == sample_series_dto.status.value


def test_create_series_defaults_optional_featured(sample_series_dto):
    author_id = uuid.uuid4()
    payload = {
        "name": {"en": "Minimal"},
    }

    mock_author = MagicMock()
    mock_author.id = author_id

    with patch(
        "pecha_api.plans.series.series_view.create_new_series",
        return_value=sample_series_dto,
    ) as mock_create, patch(
        "pecha_api.plans.series.series_service.validate_and_extract_author_details",
        return_value=mock_author,
    ):
        response = client.post(
            "/cms/series",
            json=payload,
            headers={"Authorization": "Bearer dummy"}
        )

        assert response.status_code == status.HTTP_201_CREATED
        mock_create.assert_called_once()
        assert mock_create.call_args.kwargs["create_series_request"].featured is False


def test_create_series_validation_error_missing_required_fields():
    response = client.post(
        "/cms/series",
        json={},
        headers={"Authorization": "Bearer dummy"}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_series_by_id_success(sample_series_dto):
    series_id = sample_series_dto.id
    with patch(
        "pecha_api.plans.series.public_series_view.get_series_detail",
        return_value=sample_series_dto,
    ) as mock_detail:
        response = client.get(f"/series/{series_id}")

        assert response.status_code == status.HTTP_200_OK
        mock_detail.assert_called_once_with(series_id=series_id)

        data = response.json()
        assert data["id"] == str(sample_series_dto.id)
        assert data["name"] == sample_series_dto.name
        assert data["status"] == sample_series_dto.status.value


def test_get_series_by_id_not_found():
    series_id = uuid.uuid4()
    with patch(
        "pecha_api.plans.series.public_series_view.get_series_detail",
        side_effect=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Series with id '{series_id}' not found",
        ),
    ):
        response = client.get(f"/series/{series_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_series_by_id_includes_total_days_in_response():
    series_id = uuid.uuid4()
    plan_1_id = uuid.uuid4()
    plan_2_id = uuid.uuid4()

    plan_1 = SeriesPlanDTO(
        id=plan_1_id,
        title="Plan 1",
        description="First plan",
        language=LanguageCode.EN.value,
        difficulty_level=DifficultyLevel.BEGINNER,
        image_url=None,
        image_key=None,
        tags=[],
        status=PlanStatus.DRAFT,
        featured=False,
        display_order=1,
        start_date=None,
        total_days=5,
    )

    plan_2 = SeriesPlanDTO(
        id=plan_2_id,
        title="Plan 2",
        description="Second plan",
        language=LanguageCode.EN.value,
        difficulty_level=DifficultyLevel.INTERMEDIATE,
        image_url=None,
        image_key=None,
        tags=[],
        status=PlanStatus.PUBLISHED,
        featured=False,
        display_order=2,
        start_date=None,
        total_days=3,
    )

    series_dto = SeriesDTO(
        id=series_id,
        name={"en": "Series with plans"},
        image=None,
        image_key=None,
        author_id=uuid.uuid4(),
        featured=False,
        status=PlanStatus.DRAFT,
        plans=[plan_1, plan_2],
        total_days=8,
    )

    with patch(
        "pecha_api.plans.series.public_series_view.get_series_detail",
        return_value=series_dto,
    ) as mock_detail:
        response = client.get(f"/series/{series_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        mock_detail.assert_called_once_with(series_id=series_id)

        assert data["total_days"] == 8
        assert len(data["plans"]) == 2
        assert data["plans"][0]["id"] == str(plan_1_id)
        assert data["plans"][0]["total_days"] == 5
        assert data["plans"][1]["id"] == str(plan_2_id)
        assert data["plans"][1]["total_days"] == 3


def test_get_series_list_includes_total_days_zero():
    series_id = uuid.uuid4()
    series_dto = SeriesDTO(
        id=series_id,
        name={"en": "Series without plans"},
        image=None,
        image_key=None,
        author_id=uuid.uuid4(),
        featured=False,
        status=PlanStatus.DRAFT,
        plans=[],
        total_days=0,
    )

    series_list_response = SeriesListResponse(
        series=[series_dto],
        skip=0,
        limit=10,
        total=1,
    )

    with patch(
        "pecha_api.plans.series.public_series_view.get_filtered_series",
        return_value=series_list_response,
    ):
        response = client.get("/series")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["series"]) == 1
        assert data["series"][0]["total_days"] == 0
