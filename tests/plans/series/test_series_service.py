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
    update_existing_series,
)
from pecha_api.plans.series.series_response_models import CreateSeriesRequest, UpdateSeriesRequest, SeriesListResponse


def _session_local_context(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_session_local.return_value.__exit__.return_value = False
    return mock_db


def test_get_filtered_series_maps_rows_to_response():
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

        result = get_filtered_series(search=None, skip=2, limit=5)

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


def test_get_filtered_series_presigns_image_when_key_present():
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

        result = get_filtered_series(search=None, skip=0, limit=10)

    assert result.series[0].image == "https://signed.example/x.jpg"
    assert result.series[0].image_key == "series/covers/x.jpg"
    mock_presign.assert_called_once_with(bucket_name="test-bucket", s3_key="series/covers/x.jpg")


def test_get_filtered_series_empty_repository():
    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.get_series_paginated",
        return_value=([], 0),
    ):
        _session_local_context(mock_session_local)

        result = get_filtered_series(search="nomatch", skip=0, limit=10)

    assert result.series == []
    assert result.total == 0


def test_create_new_series_persists_and_returns_dto():
    author_id = uuid.uuid4()
    request = CreateSeriesRequest(
        name={"en": "New"},
        image_key="img/key.png",
        featured=True,
    )
    saved = MagicMock()
    saved.id = uuid.uuid4()
    saved.name = request.name   
    saved.image = request.image_key
    saved.author_id = author_id
    saved.featured = True
    saved.status = PlanStatus.DRAFT

    mock_author = MagicMock()
    mock_author.id = author_id

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.save_series_with_plans",
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
    assert passed_series.image == request.image_key
    assert passed_series.author_id == author_id
    assert passed_series.featured is True

    assert dto.id == saved.id
    assert dto.name == request.name
    assert dto.image_key == request.image_key
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
        "pecha_api.plans.series.series_service.save_series_with_plans",
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
        "pecha_api.plans.series.series_service.save_series_with_plans",
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


# ---------------------------------------------------------------------------
# Helpers shared by update_existing_series tests
# ---------------------------------------------------------------------------

def _make_existing_series(series_id, author_id, plans=None):
    series = MagicMock()
    series.id = series_id
    series.author_id = author_id
    series.plans = plans or []
    return series


def _make_refreshed_series(series_id, author_id):
    refreshed = MagicMock()
    refreshed.id = series_id
    refreshed.name = {"en": "Updated"}
    refreshed.image = None
    refreshed.author_id = author_id
    refreshed.featured = False
    refreshed.status = PlanStatus.DRAFT
    refreshed.plans = []
    return refreshed


def _make_mock_author(author_id, email="author@example.com", is_admin=False):
    author = MagicMock()
    author.id = author_id
    author.email = email
    author.is_admin = is_admin
    return author


# ---------------------------------------------------------------------------
# Group 1: Plans field behavior
# ---------------------------------------------------------------------------

def test_update_existing_series_plans_omitted_leaves_attachments_untouched():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()

    plan_a = MagicMock()
    plan_a.id = uuid.uuid4()
    plan_a.deleted_at = None

    plan_b = MagicMock()
    plan_b.id = uuid.uuid4()
    plan_b.deleted_at = None

    existing = _make_existing_series(series_id, author_id, plans=[plan_a, plan_b])
    refreshed = _make_refreshed_series(series_id, author_id)
    mock_author = _make_mock_author(author_id)

    request = UpdateSeriesRequest(plans=None)

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", side_effect=[existing, refreshed]), \
         patch("pecha_api.plans.series.series_service.update_series_with_plans") as mock_update, \
         patch("pecha_api.plans.series.series_service._validate_plan_ids_for_replace") as mock_validate:
        _session_local_context(mock_session_local)
        update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    mock_validate.assert_not_called()
    call_kwargs = mock_update.call_args.kwargs
    assert call_kwargs["plan_ids_to_attach"] == []
    assert call_kwargs["plan_ids_to_detach"] == []


def test_update_existing_series_plans_empty_dict_detaches_all():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()

    plan_a_id = uuid.uuid4()
    plan_b_id = uuid.uuid4()

    plan_a = MagicMock()
    plan_a.id = plan_a_id
    plan_a.deleted_at = None

    plan_b = MagicMock()
    plan_b.id = plan_b_id
    plan_b.deleted_at = None

    existing = _make_existing_series(series_id, author_id, plans=[plan_a, plan_b])
    refreshed = _make_refreshed_series(series_id, author_id)
    mock_author = _make_mock_author(author_id)

    request = UpdateSeriesRequest(plans={})

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", side_effect=[existing, refreshed]), \
         patch("pecha_api.plans.series.series_service.update_series_with_plans") as mock_update:
        _session_local_context(mock_session_local)
        update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    call_kwargs = mock_update.call_args.kwargs
    assert call_kwargs["plan_ids_to_attach"] == []
    assert set(call_kwargs["plan_ids_to_detach"]) == {plan_a_id, plan_b_id}


def test_update_existing_series_full_replacement_with_diff():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()

    plan_a_id = uuid.uuid4()
    plan_b_id = uuid.uuid4()
    plan_c_id = uuid.uuid4()

    existing_plan_a = MagicMock()
    existing_plan_a.id = plan_a_id
    existing_plan_a.deleted_at = None

    existing_plan_b = MagicMock()
    existing_plan_b.id = plan_b_id
    existing_plan_b.deleted_at = None

    existing = _make_existing_series(series_id, author_id, plans=[existing_plan_a, existing_plan_b])
    refreshed = _make_refreshed_series(series_id, author_id)
    mock_author = _make_mock_author(author_id)

    fetched_plan_a = MagicMock()
    fetched_plan_a.id = plan_a_id
    fetched_plan_a.deleted_at = None
    fetched_plan_a.series_id = series_id
    fetched_plan_a.author_id = author_id

    fetched_plan_c = MagicMock()
    fetched_plan_c.id = plan_c_id
    fetched_plan_c.deleted_at = None
    fetched_plan_c.series_id = None
    fetched_plan_c.author_id = author_id

    request = UpdateSeriesRequest(plans={"EN": [plan_a_id, plan_c_id]})

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", side_effect=[existing, refreshed]), \
         patch("pecha_api.plans.series.series_service.get_plans_by_ids", return_value=[fetched_plan_a, fetched_plan_c]), \
         patch("pecha_api.plans.series.series_service.update_series_with_plans") as mock_update:
        _session_local_context(mock_session_local)
        update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    call_kwargs = mock_update.call_args.kwargs
    assert set(call_kwargs["plan_ids_to_attach"]) == {plan_c_id}
    assert set(call_kwargs["plan_ids_to_detach"]) == {plan_b_id}


# ---------------------------------------------------------------------------
# Group 2: Field updates
# ---------------------------------------------------------------------------

def test_update_existing_series_updates_name_image_featured():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()

    existing = _make_existing_series(series_id, author_id)
    refreshed = _make_refreshed_series(series_id, author_id)
    mock_author = _make_mock_author(author_id)

    request = UpdateSeriesRequest(name={"en": "New Name"}, image_key="covers/new.jpg", featured=True)

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", side_effect=[existing, refreshed]), \
         patch("pecha_api.plans.series.series_service.update_series_with_plans") as mock_update:
        _session_local_context(mock_session_local)
        update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    call_kwargs = mock_update.call_args.kwargs
    assert call_kwargs["name"] == {"en": "New Name"}
    assert call_kwargs["image"] == "covers/new.jpg"
    assert call_kwargs["featured"] is True


def test_update_existing_series_sets_updated_at_and_updated_by():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()

    existing = _make_existing_series(series_id, author_id)
    refreshed = _make_refreshed_series(series_id, author_id)
    mock_author = _make_mock_author(author_id, email="user@pecha.org")

    request = UpdateSeriesRequest(name={"en": "Updated"})

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", side_effect=[existing, refreshed]), \
         patch("pecha_api.plans.series.series_service.update_series_with_plans") as mock_update:
        _session_local_context(mock_session_local)
        update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    call_kwargs = mock_update.call_args.kwargs
    assert isinstance(call_kwargs["updated_at"], datetime)
    assert call_kwargs["updated_at"].tzinfo is not None
    assert call_kwargs["updated_by"] == "user@pecha.org"


def test_update_existing_series_featured_not_modified_when_none():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()

    existing = _make_existing_series(series_id, author_id)
    existing.featured = False
    refreshed = _make_refreshed_series(series_id, author_id)
    mock_author = _make_mock_author(author_id)

    request = UpdateSeriesRequest(featured=None)

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", side_effect=[existing, refreshed]), \
         patch("pecha_api.plans.series.series_service.update_series_with_plans") as mock_update:
        _session_local_context(mock_session_local)
        update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    call_kwargs = mock_update.call_args.kwargs
    assert call_kwargs["featured"] is False


# ---------------------------------------------------------------------------
# Group 3: Authorization
# ---------------------------------------------------------------------------

def test_update_existing_series_returns_404_when_series_not_found():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()
    mock_author = _make_mock_author(author_id)

    request = UpdateSeriesRequest(name={"en": "Updated"})

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", return_value=None), \
         patch("pecha_api.plans.series.series_service.update_series_with_plans") as mock_update:
        _session_local_context(mock_session_local)

        with pytest.raises(HTTPException) as exc:
            update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    mock_update.assert_not_called()


def test_update_existing_series_returns_403_when_non_admin_other_author():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()
    other_author_id = uuid.uuid4()

    existing = _make_existing_series(series_id, other_author_id)
    mock_author = _make_mock_author(author_id, is_admin=False)

    request = UpdateSeriesRequest(name={"en": "Updated"})

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", return_value=existing), \
         patch("pecha_api.plans.series.series_service.update_series_with_plans") as mock_update:
        _session_local_context(mock_session_local)

        with pytest.raises(HTTPException) as exc:
            update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    mock_update.assert_not_called()


def test_update_existing_series_admin_can_edit_other_author_series():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()
    other_author_id = uuid.uuid4()

    existing = _make_existing_series(series_id, other_author_id)
    refreshed = _make_refreshed_series(series_id, other_author_id)
    mock_author = _make_mock_author(author_id, is_admin=True)

    request = UpdateSeriesRequest(name={"en": "Admin edit"})

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", side_effect=[existing, refreshed]), \
         patch("pecha_api.plans.series.series_service.update_series_with_plans") as mock_update:
        _session_local_context(mock_session_local)
        update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    mock_update.assert_called_once()


# ---------------------------------------------------------------------------
# Group 4: Plan validation
# ---------------------------------------------------------------------------

def test_update_existing_series_400_when_plan_does_not_exist():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()
    missing_plan_id = uuid.uuid4()

    existing = _make_existing_series(series_id, author_id)
    mock_author = _make_mock_author(author_id)

    request = UpdateSeriesRequest(plans={"EN": [missing_plan_id]})

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", return_value=existing), \
         patch("pecha_api.plans.series.series_service.get_plans_by_ids", return_value=[]), \
         patch("pecha_api.plans.series.series_service.update_series_with_plans") as mock_update:
        _session_local_context(mock_session_local)

        with pytest.raises(HTTPException) as exc:
            update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "does not exist" in exc.value.detail
    mock_update.assert_not_called()


def test_update_existing_series_400_when_plan_attached_to_different_series():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    other_series_id = uuid.uuid4()

    existing = _make_existing_series(series_id, author_id)
    mock_author = _make_mock_author(author_id)

    conflicting_plan = MagicMock()
    conflicting_plan.id = plan_id
    conflicting_plan.deleted_at = None
    conflicting_plan.series_id = other_series_id
    conflicting_plan.author_id = author_id

    request = UpdateSeriesRequest(plans={"EN": [plan_id]})

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", return_value=existing), \
         patch("pecha_api.plans.series.series_service.get_plans_by_ids", return_value=[conflicting_plan]), \
         patch("pecha_api.plans.series.series_service.update_series_with_plans") as mock_update:
        _session_local_context(mock_session_local)

        with pytest.raises(HTTPException) as exc:
            update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "already attached to another series" in exc.value.detail
    mock_update.assert_not_called()


def test_update_existing_series_allows_plan_already_attached_to_current_series():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()
    plan_id = uuid.uuid4()

    existing_plan = MagicMock()
    existing_plan.id = plan_id
    existing_plan.deleted_at = None

    existing = _make_existing_series(series_id, author_id, plans=[existing_plan])
    refreshed = _make_refreshed_series(series_id, author_id)
    mock_author = _make_mock_author(author_id)

    fetched_plan = MagicMock()
    fetched_plan.id = plan_id
    fetched_plan.deleted_at = None
    fetched_plan.series_id = series_id
    fetched_plan.author_id = author_id

    request = UpdateSeriesRequest(plans={"EN": [plan_id]})

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", side_effect=[existing, refreshed]), \
         patch("pecha_api.plans.series.series_service.get_plans_by_ids", return_value=[fetched_plan]), \
         patch("pecha_api.plans.series.series_service.update_series_with_plans") as mock_update:
        _session_local_context(mock_session_local)
        update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    mock_update.assert_called_once()


def test_update_existing_series_403_when_non_admin_plan_belongs_to_other_author():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()
    other_author_id = uuid.uuid4()
    plan_id = uuid.uuid4()

    existing = _make_existing_series(series_id, author_id)
    mock_author = _make_mock_author(author_id, is_admin=False)

    other_authors_plan = MagicMock()
    other_authors_plan.id = plan_id
    other_authors_plan.deleted_at = None
    other_authors_plan.series_id = None
    other_authors_plan.author_id = other_author_id

    request = UpdateSeriesRequest(plans={"EN": [plan_id]})

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", return_value=existing), \
         patch("pecha_api.plans.series.series_service.get_plans_by_ids", return_value=[other_authors_plan]), \
         patch("pecha_api.plans.series.series_service.update_series_with_plans") as mock_update:
        _session_local_context(mock_session_local)

        with pytest.raises(HTTPException) as exc:
            update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert "belongs to another author" in exc.value.detail
    mock_update.assert_not_called()


# ---------------------------------------------------------------------------
# Group 5: Partial-update (UpdateSeriesRequest) field semantics
# ---------------------------------------------------------------------------

def test_update_existing_series_omitting_featured_keeps_existing_value():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()
    existing = _make_existing_series(series_id, author_id)
    existing.featured = True
    refreshed = _make_refreshed_series(series_id, author_id)
    mock_author = _make_mock_author(author_id)

    request = UpdateSeriesRequest(name={"en": "Renamed only"})

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", side_effect=[existing, refreshed]), \
         patch("pecha_api.plans.series.series_service.update_series_with_plans") as mock_update:
        _session_local_context(mock_session_local)
        update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    assert existing.featured is True
    assert mock_update.call_args.kwargs["featured"] is True


def test_update_existing_series_omitting_image_key_keeps_existing_image():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()
    existing = _make_existing_series(series_id, author_id)
    existing.image = "series/covers/original.jpg"
    refreshed = _make_refreshed_series(series_id, author_id)
    mock_author = _make_mock_author(author_id)

    request = UpdateSeriesRequest(featured=True)

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", side_effect=[existing, refreshed]), \
         patch("pecha_api.plans.series.series_service.update_series_with_plans") as mock_update:
        _session_local_context(mock_session_local)
        update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    assert existing.image == "series/covers/original.jpg"
    assert mock_update.call_args.kwargs["image"] == "series/covers/original.jpg"


def test_update_existing_series_omitting_all_fields_is_noop_on_scalars():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()
    existing = _make_existing_series(series_id, author_id)
    existing.name = {"en": "Original"}
    existing.image = "series/covers/original.jpg"
    existing.featured = False
    original_name = existing.name
    original_image = existing.image
    original_featured = existing.featured
    refreshed = _make_refreshed_series(series_id, author_id)
    mock_author = _make_mock_author(author_id)

    request = UpdateSeriesRequest()

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", side_effect=[existing, refreshed]), \
         patch("pecha_api.plans.series.series_service.update_series_with_plans") as mock_update:
        _session_local_context(mock_session_local)
        update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    assert existing.name == original_name
    assert existing.image == original_image
    assert existing.featured == original_featured
    mock_update.assert_called_once()
