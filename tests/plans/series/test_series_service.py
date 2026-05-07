import uuid
from unittest.mock import MagicMock, patch

import pytest

from pecha_api.plans.plans_enums import PlanStatus
from pecha_api.plans.series.series_service import create_new_series, get_filtered_series
from pecha_api.plans.series.service_response_models import CreateSeriesRequest, SeriesListResponse


def _session_local_context(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_session_local.return_value.__exit__.return_value = False
    return mock_db


@pytest.mark.asyncio
async def test_get_filtered_series_maps_rows_to_response():
    author_id = uuid.uuid4()
    row = MagicMock()
    row.id = uuid.uuid4()
    row.name = {"en": "Series A"}
    row.image = None
    row.author_id = author_id
    row.featured = True
    row.status = PlanStatus.DRAFT

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.get_series_paginated",
        return_value=([row], 1),
    ) as mock_repo:
        _session_local_context(mock_session_local)

        result = await get_filtered_series(search=None, skip=2, limit=5)

    mock_repo.assert_called_once()
    call_kwargs = mock_repo.call_args.kwargs
    assert call_kwargs["search"] is None
    assert call_kwargs["skip"] == 2
    assert call_kwargs["limit"] == 5

    assert isinstance(result, SeriesListResponse)
    assert result.skip == 2
    assert result.limit == 5
    assert result.total == 1
    assert len(result.series) == 1
    dto = result.series[0]
    assert dto.id == row.id
    assert dto.name == {"en": "Series A"}
    assert dto.image is None
    assert dto.image_key is None
    assert dto.author_id == author_id
    assert dto.featured is True
    assert dto.status == PlanStatus.DRAFT


@pytest.mark.asyncio
async def test_get_filtered_series_presigns_image_when_key_present():
    row = MagicMock()
    row.id = uuid.uuid4()
    row.name = {"en": "With cover"}
    row.image = "series/covers/x.jpg"
    row.author_id = uuid.uuid4()
    row.featured = False
    row.status = MagicMock()
    row.status.value = PlanStatus.PUBLISHED.value

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.get_series_paginated",
        return_value=([row], 1),
    ), patch("pecha_api.plans.series.series_service.get", return_value="test-bucket"), patch(
        "pecha_api.plans.series.series_service.generate_presigned_access_url",
        return_value="https://signed.example/x.jpg",
    ) as mock_presign:
        _session_local_context(mock_session_local)

        result = await get_filtered_series(search=None, skip=0, limit=10)

    assert result.series[0].image == "https://signed.example/x.jpg"
    assert result.series[0].image_key == "series/covers/x.jpg"
    mock_presign.assert_called_once_with(bucket_name="test-bucket", s3_key="series/covers/x.jpg")


@pytest.mark.asyncio
async def test_get_filtered_series_empty_repository():
    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.get_series_paginated",
        return_value=([], 0),
    ):
        _session_local_context(mock_session_local)

        result = await get_filtered_series(search="nomatch", skip=0, limit=10)

    assert result.series == []
    assert result.total == 0


def test_create_new_series_persists_and_returns_dto():
    author_id = uuid.uuid4()
    request = CreateSeriesRequest(
        name={"en": "New"},
        author_id=author_id,
        created_by="cms@example.com",
        image="img/key.png",
        featured=True,
    )
    saved = MagicMock()
    saved.id = uuid.uuid4()
    saved.name = request.name
    saved.image = request.image
    saved.author_id = author_id
    saved.featured = True
    saved.status = PlanStatus.DRAFT

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.save_series",
        return_value=saved,
    ) as mock_save, patch("pecha_api.plans.series.series_service.get", return_value="b"), patch(
        "pecha_api.plans.series.series_service.generate_presigned_access_url",
        return_value="https://signed/img.png",
    ):
        _session_local_context(mock_session_local)

        dto = create_new_series(create_series_request=request)

    mock_save.assert_called_once()
    passed_series = mock_save.call_args.kwargs["series"]
    assert passed_series.name == request.name
    assert passed_series.image == request.image
    assert passed_series.author_id == author_id
    assert passed_series.featured is True
    assert passed_series.created_by == request.created_by

    assert dto.id == saved.id
    assert dto.name == request.name
    assert dto.image_key == request.image
    assert dto.featured is True
    assert dto.status == PlanStatus.DRAFT


def test_create_new_series_featured_defaults_when_none():
    author_id = uuid.uuid4()
    request = CreateSeriesRequest(
        name={"bo": "བོད་"},
        author_id=author_id,
        created_by="user@test.com",
        featured=None,
    )
    saved = MagicMock()
    saved.id = uuid.uuid4()
    saved.name = request.name
    saved.image = None
    saved.author_id = author_id
    saved.featured = False
    saved.status = PlanStatus.DRAFT

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.save_series",
        return_value=saved,
    ) as mock_save:
        _session_local_context(mock_session_local)

        create_new_series(create_series_request=request)

    passed_series = mock_save.call_args.kwargs["series"]
    assert passed_series.featured is False
