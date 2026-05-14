import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from starlette import status

from pecha_api.plans.plans_enums import DifficultyLevel, LanguageCode, PlanStatus
from pecha_api.plans.series.series_model import Series
from pecha_api.plans.series.series_service import (
    create_new_series,
    get_filtered_series,
    get_series_detail,
)
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
    row.plans = None

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
    assert call_kwargs["include_deleted"] is False
    assert call_kwargs["order_by_field"] == Series.created_at
    assert call_kwargs["order_desc"] is True

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

    mock_author = MagicMock()
    mock_author.id = author_id

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.save_series",
        return_value=saved,
    ) as mock_save, patch("pecha_api.plans.series.series_service.get", return_value="b"), patch(
        "pecha_api.plans.series.series_service.generate_presigned_access_url",
        return_value="https://signed/img.png",
    ), patch(
        "pecha_api.plans.series.series_service.validate_and_extract_author_details",
        return_value=mock_author,
    ):
        _session_local_context(mock_session_local)

        dto = create_new_series(token="dummy", create_series_request=request)

    mock_save.assert_called_once()
    passed_series = mock_save.call_args.kwargs["series"]
    assert passed_series.name == request.name
    assert passed_series.image == request.image
    assert passed_series.author_id == author_id
    assert passed_series.featured is True

    assert dto.id == saved.id
    assert dto.name == request.name
    assert dto.image_key == request.image
    assert dto.featured is True
    assert dto.status == PlanStatus.DRAFT


def test_create_new_series_featured_defaults_when_none():
    author_id = uuid.uuid4()
    request = CreateSeriesRequest(
        name={"bo": "བོད་"},
        featured=None,
    )
    saved = MagicMock()
    saved.id = uuid.uuid4()
    saved.name = request.name
    saved.image = None
    saved.author_id = author_id
    saved.featured = False
    saved.status = PlanStatus.DRAFT

    mock_author = MagicMock()
    mock_author.id = author_id

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.save_series",
        return_value=saved,
    ) as mock_save, patch(
        "pecha_api.plans.series.series_service.validate_and_extract_author_details",
        return_value=mock_author,
    ):
        _session_local_context(mock_session_local)

        create_new_series(token="dummy", create_series_request=request)

    passed_series = mock_save.call_args.kwargs["series"]
    assert passed_series.featured is False


def test_create_new_series_integrity_error_raises_400():
    author_id = uuid.uuid4()
    request = CreateSeriesRequest(
        name={"en": "Test"},
    )
    orig = Exception("foreign key violation")

    mock_author = MagicMock()
    mock_author.id = author_id

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.save_series",
        side_effect=IntegrityError("statement", {}, orig),
    ), patch(
        "pecha_api.plans.series.series_service.validate_and_extract_author_details",
        return_value=mock_author,
    ):
        _session_local_context(mock_session_local)

        with pytest.raises(HTTPException) as exc:
            create_new_series(token="dummy", create_series_request=request)

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Database integrity error" in exc.value.detail


def test_get_series_detail_raises_404_when_not_found():
    series_id = uuid.uuid4()
    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.get_series_by_id",
        return_value=None,
    ):
        _session_local_context(mock_session_local)

        with pytest.raises(HTTPException) as exc:
            get_series_detail(series_id=series_id)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert str(series_id) in exc.value.detail


def test_get_series_detail_returns_dto_without_plans():
    series_id = uuid.uuid4()
    row = MagicMock()
    row.id = series_id
    row.name = {"en": "Only series"}
    row.image = None
    row.author_id = uuid.uuid4()
    row.featured = False
    row.status = PlanStatus.DRAFT
    row.plans = []

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.get_series_by_id",
        return_value=row,
    ):
        _session_local_context(mock_session_local)

        dto = get_series_detail(series_id=series_id)

    assert dto.id == series_id
    assert dto.plans == []


def test_get_series_detail_includes_active_plans_sorted_and_presigns_images():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()
    plan_b_id = uuid.uuid4()
    plan_a_id = uuid.uuid4()

    deleted_plan = MagicMock()
    deleted_plan.deleted_at = datetime.now(timezone.utc)
    deleted_plan.display_order = 0

    plan_b = MagicMock()
    plan_b.deleted_at = None
    plan_b.display_order = 2
    plan_b.id = plan_b_id
    plan_b.title = "Second order"
    plan_b.description = None
    plan_b.language = LanguageCode.EN
    plan_b.difficulty_level = DifficultyLevel.BEGINNER
    plan_b.image_url = "plans/b.jpg"
    plan_b.tags = ["x"]
    plan_b.status = PlanStatus.DRAFT
    plan_b.featured = False
    plan_b.start_date = None

    plan_a = MagicMock()
    plan_a.deleted_at = None
    plan_a.display_order = 1
    plan_a.id = plan_a_id
    plan_a.title = "First order"
    plan_a.description = "Desc"
    plan_a.language = LanguageCode.BO
    plan_a.difficulty_level = None
    plan_a.image_url = None
    plan_a.tags = None
    plan_a.status = MagicMock()
    plan_a.status.value = PlanStatus.PUBLISHED.value
    plan_a.featured = 1
    plan_a.start_date = None

    row = MagicMock()
    row.id = series_id
    row.name = {"en": "With plans"}
    row.image = None
    row.author_id = author_id
    row.featured = True
    row.status = PlanStatus.PUBLISHED
    row.plans = [deleted_plan, plan_b, plan_a]

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.get_series_by_id",
        return_value=row,
    ), patch("pecha_api.plans.series.series_service.get", return_value="bk"), patch(
        "pecha_api.plans.series.series_service.generate_presigned_access_url",
        return_value="https://signed/b.jpg",
    ) as mock_presign:
        _session_local_context(mock_session_local)

        dto = get_series_detail(series_id=series_id)

    assert len(dto.plans) == 2
    assert dto.plans[0].id == plan_a_id
    assert dto.plans[0].title == "First order"
    assert dto.plans[0].image_url is None
    assert dto.plans[0].image_key is None
    assert dto.plans[0].tags == []
    assert dto.plans[0].status == PlanStatus.PUBLISHED
    assert dto.plans[0].featured is True

    assert dto.plans[1].id == plan_b_id
    assert dto.plans[1].image_url == "https://signed/b.jpg"
    assert dto.plans[1].image_key == "plans/b.jpg"
    mock_presign.assert_called_once_with(bucket_name="bk", s3_key="plans/b.jpg")


def test_get_series_detail_includes_total_days_for_each_plan():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()

    item_1 = MagicMock()
    item_2 = MagicMock()
    item_3 = MagicMock()

    plan_a = MagicMock()
    plan_a.deleted_at = None
    plan_a.display_order = 1
    plan_a.id = uuid.uuid4()
    plan_a.title = "Plan A"
    plan_a.description = "First plan"
    plan_a.language = LanguageCode.EN
    plan_a.difficulty_level = DifficultyLevel.BEGINNER
    plan_a.image_url = None
    plan_a.tags = []
    plan_a.status = PlanStatus.DRAFT
    plan_a.featured = False
    plan_a.start_date = None
    plan_a.items = [item_1, item_2, item_3]

    item_4 = MagicMock()
    item_5 = MagicMock()

    plan_b = MagicMock()
    plan_b.deleted_at = None
    plan_b.display_order = 2
    plan_b.id = uuid.uuid4()
    plan_b.title = "Plan B"
    plan_b.description = "Second plan"
    plan_b.language = LanguageCode.EN
    plan_b.difficulty_level = DifficultyLevel.INTERMEDIATE
    plan_b.image_url = None
    plan_b.tags = []
    plan_b.status = PlanStatus.PUBLISHED
    plan_b.featured = False
    plan_b.start_date = None
    plan_b.items = [item_4, item_5]

    row = MagicMock()
    row.id = series_id
    row.name = {"en": "Series with day counts"}
    row.image = None
    row.author_id = author_id
    row.featured = False
    row.status = PlanStatus.DRAFT
    row.plans = [plan_a, plan_b]

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.get_series_by_id",
        return_value=row,
    ):
        _session_local_context(mock_session_local)

        dto = get_series_detail(series_id=series_id)

    assert len(dto.plans) == 2
    assert dto.plans[0].total_days == 3
    assert dto.plans[1].total_days == 2
    assert dto.total_days == 5


def test_get_series_detail_total_days_zero_when_no_items():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()

    plan_empty = MagicMock()
    plan_empty.deleted_at = None
    plan_empty.display_order = 1
    plan_empty.id = uuid.uuid4()
    plan_empty.title = "Empty Plan"
    plan_empty.description = None
    plan_empty.language = LanguageCode.EN
    plan_empty.difficulty_level = DifficultyLevel.BEGINNER
    plan_empty.image_url = None
    plan_empty.tags = []
    plan_empty.status = PlanStatus.DRAFT
    plan_empty.featured = False
    plan_empty.start_date = None
    plan_empty.items = []

    row = MagicMock()
    row.id = series_id
    row.name = {"en": "Series with empty plan"}
    row.image = None
    row.author_id = author_id
    row.featured = False
    row.status = PlanStatus.DRAFT
    row.plans = [plan_empty]

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.get_series_by_id",
        return_value=row,
    ):
        _session_local_context(mock_session_local)

        dto = get_series_detail(series_id=series_id)

    assert len(dto.plans) == 1
    assert dto.plans[0].total_days == 0
    assert dto.total_days == 0


def test_get_series_detail_total_days_zero_when_no_plans():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()

    row = MagicMock()
    row.id = series_id
    row.name = {"en": "Series without plans"}
    row.image = None
    row.author_id = author_id
    row.featured = False
    row.status = PlanStatus.DRAFT
    row.plans = []

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.get_series_by_id",
        return_value=row,
    ):
        _session_local_context(mock_session_local)

        dto = get_series_detail(series_id=series_id)

    assert dto.plans == []
    assert dto.total_days == 0


def test_get_series_detail_handles_plan_without_items_attribute():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()

    plan_no_items = MagicMock(spec=["deleted_at", "display_order", "id", "title", "description", 
                                     "language", "difficulty_level", "image_url", "tags", 
                                     "status", "featured", "start_date"])
    plan_no_items.deleted_at = None
    plan_no_items.display_order = 1
    plan_no_items.id = uuid.uuid4()
    plan_no_items.title = "Plan without items"
    plan_no_items.description = None
    plan_no_items.language = LanguageCode.EN
    plan_no_items.difficulty_level = DifficultyLevel.BEGINNER
    plan_no_items.image_url = None
    plan_no_items.tags = []
    plan_no_items.status = PlanStatus.DRAFT
    plan_no_items.featured = False
    plan_no_items.start_date = None

    row = MagicMock()
    row.id = series_id
    row.name = {"en": "Series with plan without items"}
    row.image = None
    row.author_id = author_id
    row.featured = False
    row.status = PlanStatus.DRAFT
    row.plans = [plan_no_items]

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.get_series_by_id",
        return_value=row,
    ):
        _session_local_context(mock_session_local)

        dto = get_series_detail(series_id=series_id)

    assert len(dto.plans) == 1
    assert dto.plans[0].total_days == 0
    assert dto.total_days == 0
