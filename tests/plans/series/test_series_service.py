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
    _validate_plan_ids,
    _build_plan_order_pairs,
    create_new_series,
    get_filtered_series,
    get_series_detail,
    update_existing_series,
    get_cms_filtered_series,
    get_cms_series_detail,
)
from pecha_api.plans.series.series_response_models import (
    CreateSeriesRequest,
    UpdateSeriesRequest,
    SeriesListItemDTO,
    SeriesListResponse,
    SeriesMetadataInput,
)


def _metadata_entry(title="Series A", language=LanguageCode.EN, description=None):
    entry = MagicMock()
    entry.id = uuid.uuid4()
    entry.title = title
    entry.description = description
    entry.language = language
    return entry


def _metadata_input(title="Series A", language=LanguageCode.EN, description=None):
    return SeriesMetadataInput(title=title, description=description, language=language)


def _session_local_context(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_session_local.return_value.__exit__.return_value = False
    return mock_db


def test_get_filtered_series_maps_rows_to_response():
    author_id = uuid.uuid4()
    row = MagicMock()
    row.id = uuid.uuid4()
    row.metadata_entries = [_metadata_entry(title="Series A")]
    row.image = None
    row.author_id = author_id
    row.featured = True
    row.status = PlanStatus.DRAFT
    row.plans = None

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.get_series_paginated",
        return_value=([(row, 3)], 1),
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
    assert call_kwargs["status"] == PlanStatus.PUBLISHED

    assert isinstance(result, SeriesListResponse)
    assert result.skip == 2
    assert result.limit == 5
    assert result.total == 1
    assert len(result.series) == 1
    dto = result.series[0]
    assert dto.id == row.id
    assert len(dto.metadata) == 1
    assert dto.metadata[0].title == "Series A"
    assert dto.metadata[0].language == "EN"
    assert dto.image is None
    assert dto.image_key is None
    assert dto.author_id == author_id
    assert dto.featured is True
    assert dto.status == PlanStatus.DRAFT
    assert dto.plan_count == 3
    assert isinstance(dto, SeriesListItemDTO)
    assert "plans" not in SeriesListItemDTO.model_fields


def test_get_filtered_series_presigns_image_when_key_present():
    row = MagicMock()
    row.id = uuid.uuid4()
    row.metadata_entries = [_metadata_entry(title="With cover")]
    row.image = "series/covers/x.jpg"
    row.author_id = uuid.uuid4()
    row.featured = False
    row.status = MagicMock()
    row.status.value = PlanStatus.PUBLISHED.value

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.get_series_paginated",
        return_value=([(row, 0)], 1),
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
        metadata=[_metadata_input(title="New")],
        image_key="img/key.png",
        featured=True,
    )
    saved = MagicMock()
    saved.id = uuid.uuid4()
    saved.metadata_entries = [_metadata_entry(title="New")]
    saved.image = request.image_key
    saved.author_id = author_id
    saved.featured = True
    saved.status = PlanStatus.DRAFT

    mock_author = MagicMock()
    mock_author.id = author_id

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.save_series_with_plans",
        return_value=saved,
    ) as mock_save, patch(
        "pecha_api.plans.series.series_service.get_series_by_id",
        return_value=saved,
    ), patch("pecha_api.plans.series.series_service.get", return_value="b"), patch(
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
    assert mock_save.call_args.kwargs["metadata_entries"] == request.metadata
    assert passed_series.image == request.image_key
    assert passed_series.author_id == author_id
    assert passed_series.featured is True

    assert dto.id == saved.id
    assert dto.metadata[0].title == "New"
    assert dto.image_key == request.image_key
    assert dto.featured is True
    assert dto.status == PlanStatus.DRAFT


def test_create_new_series_featured_defaults_when_none():
    author_id = uuid.uuid4()
    request = CreateSeriesRequest(
        metadata=[_metadata_input(title="བོད་", language=LanguageCode.BO)],
        featured=None,
    )
    saved = MagicMock()
    saved.id = uuid.uuid4()
    saved.metadata_entries = [_metadata_entry(title="བོད་", language=LanguageCode.BO)]
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
        "pecha_api.plans.series.series_service.get_series_by_id",
        return_value=saved,
    ), patch(
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
        metadata=[_metadata_input(title="Test")],
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


def test_get_series_detail_raises_404_when_not_published():
    series_id = uuid.uuid4()
    row = MagicMock()
    row.id = series_id
    row.status = PlanStatus.DRAFT

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.get_series_by_id",
        return_value=row,
    ):
        _session_local_context(mock_session_local)

        with pytest.raises(HTTPException) as exc:
            get_series_detail(series_id=series_id)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_get_series_detail_returns_dto_without_plans():
    series_id = uuid.uuid4()
    row = MagicMock()
    row.id = series_id
    row.metadata_entries = [_metadata_entry(title="Only series")]
    row.image = None
    row.author_id = uuid.uuid4()
    row.featured = False
    row.status = PlanStatus.PUBLISHED
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
    plan_b.tag_list = []
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
    plan_a.tag_list = None
    plan_a.status = MagicMock()
    plan_a.status.value = PlanStatus.PUBLISHED.value
    plan_a.featured = 1
    plan_a.start_date = None

    row = MagicMock()
    row.id = series_id
    row.metadata_entries = [_metadata_entry(title="With plans")]
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
    plan_a.tag_list = []
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
    plan_b.tag_list = []
    plan_b.status = PlanStatus.PUBLISHED
    plan_b.featured = False
    plan_b.start_date = None
    plan_b.items = [item_4, item_5]

    row = MagicMock()
    row.id = series_id
    row.metadata_entries = [_metadata_entry(title="Series with day counts")]
    row.image = None
    row.author_id = author_id
    row.featured = False
    row.status = PlanStatus.PUBLISHED
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
    plan_empty.tag_list = []
    plan_empty.status = PlanStatus.DRAFT
    plan_empty.featured = False
    plan_empty.start_date = None
    plan_empty.items = []

    row = MagicMock()
    row.id = series_id
    row.metadata_entries = [_metadata_entry(title="Series with empty plan")]
    row.image = None
    row.author_id = author_id
    row.featured = False
    row.status = PlanStatus.PUBLISHED
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
    row.metadata_entries = [_metadata_entry(title="Series without plans")]
    row.image = None
    row.author_id = author_id
    row.featured = False
    row.status = PlanStatus.PUBLISHED
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
                                     "language", "difficulty_level", "image_url", "tag_list", 
                                     "status", "featured", "start_date"])
    plan_no_items.deleted_at = None
    plan_no_items.display_order = 1
    plan_no_items.id = uuid.uuid4()
    plan_no_items.title = "Plan without items"
    plan_no_items.description = None
    plan_no_items.language = LanguageCode.EN
    plan_no_items.difficulty_level = DifficultyLevel.BEGINNER
    plan_no_items.image_url = None
    plan_no_items.tag_list = []
    plan_no_items.status = PlanStatus.DRAFT
    plan_no_items.featured = False
    plan_no_items.start_date = None

    row = MagicMock()
    row.id = series_id
    row.metadata_entries = [_metadata_entry(title="Series with plan without items")]
    row.image = None
    row.author_id = author_id
    row.featured = False
    row.status = PlanStatus.PUBLISHED
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
    refreshed.metadata_entries = [_metadata_entry(title="Updated")]
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
         patch("pecha_api.plans.series.series_service._validate_plan_ids") as mock_validate:
        _session_local_context(mock_session_local)
        update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    mock_validate.assert_not_called()
    call_kwargs = mock_update.call_args.kwargs
    assert call_kwargs["plans_to_attach"] == []
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
    assert call_kwargs["plans_to_attach"] == []
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
    plans_to_attach = call_kwargs["plans_to_attach"]
    assert plans_to_attach == [(plan_a_id, 0), (plan_c_id, 1)]
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

    request = UpdateSeriesRequest(
        metadata=[_metadata_input(title="New Name")],
        image_key="covers/new.jpg",
        featured=True,
    )

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", side_effect=[existing, refreshed]), \
         patch("pecha_api.plans.series.series_service.update_series_with_plans") as mock_update:
        _session_local_context(mock_session_local)
        update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    call_kwargs = mock_update.call_args.kwargs
    assert call_kwargs["metadata_entries"] == request.metadata
    assert call_kwargs["image"] == "covers/new.jpg"
    assert call_kwargs["featured"] is True


def test_update_existing_series_sets_updated_at_and_updated_by():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()

    existing = _make_existing_series(series_id, author_id)
    refreshed = _make_refreshed_series(series_id, author_id)
    mock_author = _make_mock_author(author_id, email="user@pecha.org")

    request = UpdateSeriesRequest(metadata=[_metadata_input(title="Updated")])

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

    request = UpdateSeriesRequest(metadata=[_metadata_input(title="Updated")])

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

    request = UpdateSeriesRequest(metadata=[_metadata_input(title="Updated")])

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

    request = UpdateSeriesRequest(metadata=[_metadata_input(title="Admin edit")])

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

    request = UpdateSeriesRequest(metadata=[_metadata_input(title="Renamed only")])

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
    existing.metadata_entries = [_metadata_entry(title="Original")]
    existing.image = "series/covers/original.jpg"
    existing.featured = False
    original_metadata = list(existing.metadata_entries)
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

    assert existing.metadata_entries == original_metadata
    assert existing.image == original_image
    assert existing.featured == original_featured
    mock_update.assert_called_once()


# ---------------------------------------------------------------------------
# Group 6: Additional coverage tests
# ---------------------------------------------------------------------------

def test_update_existing_series_integrity_error_raises_400():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()
    orig = Exception("foreign key violation")

    existing = _make_existing_series(series_id, author_id)
    mock_author = _make_mock_author(author_id)

    request = UpdateSeriesRequest(metadata=[_metadata_input(title="Updated")])

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", return_value=existing), \
         patch("pecha_api.plans.series.series_service.update_series_with_plans",
               side_effect=IntegrityError("statement", {}, orig)):
        _session_local_context(mock_session_local)

        with pytest.raises(HTTPException) as exc:
            update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Database integrity error" in exc.value.detail


def test_create_new_series_with_plans_attaches_and_returns_dto():
    author_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    series_id = uuid.uuid4()

    request = CreateSeriesRequest(
        metadata=[_metadata_input(title="Series with plan")],
        plans={"EN": [plan_id]},
    )

    mock_author = _make_mock_author(author_id)

    valid_plan = MagicMock()
    valid_plan.id = plan_id
    valid_plan.deleted_at = None
    valid_plan.series_id = None
    valid_plan.author_id = author_id
    valid_plan.status = PlanStatus.DRAFT
    valid_plan.title = "Test Plan"
    valid_plan.description = None
    valid_plan.language = LanguageCode.EN
    valid_plan.difficulty_level = DifficultyLevel.BEGINNER
    valid_plan.image_url = None
    valid_plan.tag_list = []
    valid_plan.items = []
    valid_plan.featured = False
    valid_plan.display_order = None
    valid_plan.start_date = None

    saved = MagicMock()
    saved.id = series_id
    saved.metadata_entries = [_metadata_entry(title="Series with plan")]
    saved.image = None
    saved.author_id = author_id
    saved.featured = False
    saved.status = PlanStatus.DRAFT

    refreshed = MagicMock()
    refreshed.id = series_id
    refreshed.metadata_entries = [_metadata_entry(title="Series with plan")]
    refreshed.image = None
    refreshed.author_id = author_id
    refreshed.featured = False
    refreshed.status = PlanStatus.DRAFT
    refreshed.plans = [valid_plan]

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_plans_by_ids", return_value=[valid_plan]), \
         patch("pecha_api.plans.series.series_service.save_series_with_plans", return_value=saved) as mock_save, \
         patch("pecha_api.plans.series.series_service.get_series_by_id", return_value=refreshed):
        _session_local_context(mock_session_local)
        dto = create_new_series(token="dummy", create_series_request=request)

    mock_save.assert_called_once()
    assert mock_save.call_args.kwargs["plans_to_attach"] == [(plan_id, 0)]
    assert dto.id == series_id


def test_create_new_series_rejects_soft_deleted_plan():
    author_id = uuid.uuid4()
    plan_id = uuid.uuid4()

    request = CreateSeriesRequest(
        metadata=[_metadata_input(title="Series")],
        plans={"EN": [plan_id]},
    )

    mock_author = _make_mock_author(author_id)

    deleted_plan = MagicMock()
    deleted_plan.id = plan_id
    deleted_plan.deleted_at = datetime.now(timezone.utc)
    deleted_plan.series_id = None
    deleted_plan.author_id = author_id

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_plans_by_ids", return_value=[deleted_plan]), \
         patch("pecha_api.plans.series.series_service.save_series_with_plans") as mock_save:
        _session_local_context(mock_session_local)

        with pytest.raises(HTTPException) as exc:
            create_new_series(token="dummy", create_series_request=request)

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "does not exist" in exc.value.detail
    mock_save.assert_not_called()


def test_create_new_series_rejects_plan_already_attached_to_another_series():
    author_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    other_series_id = uuid.uuid4()

    request = CreateSeriesRequest(
        metadata=[_metadata_input(title="Series")],
        plans={"EN": [plan_id]},
    )

    mock_author = _make_mock_author(author_id)

    attached_plan = MagicMock()
    attached_plan.id = plan_id
    attached_plan.deleted_at = None
    attached_plan.series_id = other_series_id
    attached_plan.author_id = author_id

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_plans_by_ids", return_value=[attached_plan]), \
         patch("pecha_api.plans.series.series_service.save_series_with_plans") as mock_save:
        _session_local_context(mock_session_local)

        with pytest.raises(HTTPException) as exc:
            create_new_series(token="dummy", create_series_request=request)

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "already attached to another series" in exc.value.detail
    mock_save.assert_not_called()


def test_create_new_series_rejects_plan_belonging_to_other_author_non_admin():
    author_id = uuid.uuid4()
    other_author_id = uuid.uuid4()
    plan_id = uuid.uuid4()

    request = CreateSeriesRequest(
        metadata=[_metadata_input(title="Series")],
        plans={"EN": [plan_id]},
    )

    mock_author = _make_mock_author(author_id, is_admin=False)

    other_authors_plan = MagicMock()
    other_authors_plan.id = plan_id
    other_authors_plan.deleted_at = None
    other_authors_plan.series_id = None
    other_authors_plan.author_id = other_author_id

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_plans_by_ids", return_value=[other_authors_plan]), \
         patch("pecha_api.plans.series.series_service.save_series_with_plans") as mock_save:
        _session_local_context(mock_session_local)

        with pytest.raises(HTTPException) as exc:
            create_new_series(token="dummy", create_series_request=request)

    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert "belongs to another author" in exc.value.detail
    mock_save.assert_not_called()


def test_validate_plan_ids_dedupes_before_fetching():
    author_id = uuid.uuid4()
    plan_id = uuid.uuid4()

    request = CreateSeriesRequest(
        metadata=[_metadata_input(title="Series")],
        plans={"EN": [plan_id], "BO": [plan_id]},
    )

    mock_author = _make_mock_author(author_id)

    valid_plan = MagicMock()
    valid_plan.id = plan_id
    valid_plan.deleted_at = None
    valid_plan.series_id = None
    valid_plan.author_id = author_id
    valid_plan.status = PlanStatus.DRAFT
    valid_plan.title = "Test Plan"
    valid_plan.description = None
    valid_plan.language = LanguageCode.EN
    valid_plan.difficulty_level = DifficultyLevel.BEGINNER
    valid_plan.image_url = None
    valid_plan.tag_list = []
    valid_plan.items = []
    valid_plan.featured = False
    valid_plan.display_order = None
    valid_plan.start_date = None

    saved = MagicMock()
    saved.id = uuid.uuid4()
    saved.metadata_entries = [_metadata_entry(title="Series")]
    saved.image = None
    saved.author_id = author_id
    saved.featured = False
    saved.status = PlanStatus.DRAFT

    refreshed = MagicMock()
    refreshed.id = saved.id
    refreshed.metadata_entries = [_metadata_entry(title="Series")]
    refreshed.image = None
    refreshed.author_id = author_id
    refreshed.featured = False
    refreshed.status = PlanStatus.DRAFT
    refreshed.plans = [valid_plan]

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_plans_by_ids", return_value=[valid_plan]) as mock_get_plans, \
         patch("pecha_api.plans.series.series_service.save_series_with_plans", return_value=saved), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", return_value=refreshed):
        _session_local_context(mock_session_local)
        create_new_series(token="dummy", create_series_request=request)

    mock_get_plans.assert_called_once()
    fetched_ids = mock_get_plans.call_args.kwargs["plan_ids"]
    assert fetched_ids.count(plan_id) == 1


# ---------------------------------------------------------------------------
# CMS GET endpoints — get_cms_filtered_series
# ---------------------------------------------------------------------------

def test_get_cms_filtered_series_scopes_to_current_author_when_not_admin():
    author_id = uuid.uuid4()
    row = MagicMock()
    row.id = uuid.uuid4()
    row.name = {"en": "Mine"}
    row.image = None
    row.author_id = author_id
    row.featured = False
    row.status = PlanStatus.DRAFT
    row.plans = None

    mock_author = _make_mock_author(author_id, is_admin=False)

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_paginated",
               return_value=([(row, 2)], 1)) as mock_repo:
        _session_local_context(mock_session_local)

        result = get_cms_filtered_series(token="dummy", search=None, skip=0, limit=10)

    call_kwargs = mock_repo.call_args.kwargs
    assert call_kwargs["author_id"] == author_id
    assert call_kwargs["search"] is None
    assert call_kwargs["skip"] == 0
    assert call_kwargs["limit"] == 10
    assert call_kwargs["order_by_field"] == Series.created_at
    assert call_kwargs["order_desc"] is True

    assert isinstance(result, SeriesListResponse)
    assert result.total == 1
    assert len(result.series) == 1
    assert result.series[0].plan_count == 2


def test_get_cms_filtered_series_admin_sees_all_authors():
    admin_id = uuid.uuid4()
    row = MagicMock()
    row.id = uuid.uuid4()
    row.name = {"en": "Someone else's"}
    row.image = None
    row.author_id = uuid.uuid4()
    row.featured = False
    row.status = PlanStatus.DRAFT
    row.plans = None

    mock_admin = _make_mock_author(admin_id, is_admin=True)

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_admin), \
         patch("pecha_api.plans.series.series_service.get_series_paginated",
               return_value=([(row, 0)], 1)) as mock_repo:
        _session_local_context(mock_session_local)

        get_cms_filtered_series(token="dummy", search=None, skip=0, limit=10)

    call_kwargs = mock_repo.call_args.kwargs
    assert call_kwargs["author_id"] is None


def test_get_cms_filtered_series_passes_search_and_pagination():
    author_id = uuid.uuid4()
    mock_author = _make_mock_author(author_id, is_admin=False)

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_paginated",
               return_value=([], 0)) as mock_repo:
        _session_local_context(mock_session_local)

        get_cms_filtered_series(token="dummy", search="meditation", skip=5, limit=20)

    call_kwargs = mock_repo.call_args.kwargs
    assert call_kwargs["search"] == "meditation"
    assert call_kwargs["skip"] == 5
    assert call_kwargs["limit"] == 20
    assert call_kwargs["author_id"] == author_id


def test_get_filtered_series_passes_language_to_repository():
    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.get_series_paginated",
               return_value=([], 0)) as mock_repo:
        _session_local_context(mock_session_local)

        get_filtered_series(search=None, skip=0, limit=10, language="zh")

    call_kwargs = mock_repo.call_args.kwargs
    assert call_kwargs["language"] == "zh"
    assert call_kwargs["status"] == PlanStatus.PUBLISHED


def test_get_cms_filtered_series_passes_language_to_repository():
    author_id = uuid.uuid4()
    mock_author = _make_mock_author(author_id, is_admin=False)

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_paginated",
               return_value=([], 0)) as mock_repo:
        _session_local_context(mock_session_local)

        get_cms_filtered_series(token="dummy", search=None, skip=0, limit=10, language="en")

    assert mock_repo.call_args.kwargs["language"] == "en"


def test_get_cms_filtered_series_admin_passes_status_featured_and_author_filters():
    admin_id = uuid.uuid4()
    filter_author_id = uuid.uuid4()
    mock_admin = _make_mock_author(admin_id, is_admin=True)

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_admin), \
         patch("pecha_api.plans.series.series_service.get_series_paginated",
               return_value=([], 0)) as mock_repo:
        _session_local_context(mock_session_local)

        get_cms_filtered_series(
            token="dummy",
            search=None,
            skip=0,
            limit=10,
            plan_status=PlanStatus.DRAFT,
            featured=False,
            filter_author_id=filter_author_id,
        )

    call_kwargs = mock_repo.call_args.kwargs
    assert call_kwargs["author_id"] == filter_author_id
    assert call_kwargs["status"] == PlanStatus.DRAFT
    assert call_kwargs["featured"] is False


def test_get_cms_filtered_series_non_admin_cannot_filter_by_other_author():
    author_id = uuid.uuid4()
    other_author_id = uuid.uuid4()
    mock_author = _make_mock_author(author_id, is_admin=False)

    with patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author):
        with pytest.raises(HTTPException) as exc_info:
            get_cms_filtered_series(
                token="dummy",
                search=None,
                skip=0,
                limit=10,
                filter_author_id=other_author_id,
            )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# CMS GET endpoints — get_cms_series_detail
# ---------------------------------------------------------------------------

def test_get_cms_series_detail_returns_dto_when_owner():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()

    row = MagicMock()
    row.id = series_id
    row.name = {"en": "Mine"}
    row.image = None
    row.author_id = author_id
    row.featured = False
    row.status = PlanStatus.DRAFT
    row.plans = []

    mock_author = _make_mock_author(author_id, is_admin=False)

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", return_value=row):
        _session_local_context(mock_session_local)

        dto = get_cms_series_detail(token="dummy", series_id=series_id)

    assert dto.id == series_id
    assert dto.author_id == author_id


def test_get_cms_series_detail_raises_404_when_not_found():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()
    mock_author = _make_mock_author(author_id)

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", return_value=None):
        _session_local_context(mock_session_local)

        with pytest.raises(HTTPException) as exc:
            get_cms_series_detail(token="dummy", series_id=series_id)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert str(series_id) in exc.value.detail


def test_get_cms_series_detail_raises_403_when_non_admin_other_author():
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()
    other_author_id = uuid.uuid4()

    row = MagicMock()
    row.id = series_id
    row.author_id = other_author_id

    mock_author = _make_mock_author(author_id, is_admin=False)

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", return_value=row):
        _session_local_context(mock_session_local)

        with pytest.raises(HTTPException) as exc:
            get_cms_series_detail(token="dummy", series_id=series_id)

    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_get_cms_series_detail_admin_can_view_other_author_series():
    series_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    other_author_id = uuid.uuid4()

    row = MagicMock()
    row.id = series_id
    row.name = {"en": "Someone else's"}
    row.image = None
    row.author_id = other_author_id
    row.featured = False
    row.status = PlanStatus.DRAFT
    row.plans = []

    mock_admin = _make_mock_author(admin_id, is_admin=True)

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_admin), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", return_value=row):
        _session_local_context(mock_session_local)

        dto = get_cms_series_detail(token="dummy", series_id=series_id)

    assert dto.id == series_id
    assert dto.author_id == other_author_id


def test_get_filtered_series_handles_plain_string_status_and_language():
    row = MagicMock()
    row.id = uuid.uuid4()
    row.metadata_entries = []
    row.image = None
    row.author_id = uuid.uuid4()
    row.featured = False
    row.status = PlanStatus.DRAFT.value
    row.plans = None

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.get_series_paginated",
        return_value=([(row, 0)], 1),
    ):
        _session_local_context(mock_session_local)

        result = get_filtered_series(search=None, skip=0, limit=10)

    assert result.total == 1
    assert result.series[0].status == PlanStatus.DRAFT
    assert result.series[0].metadata == []


def test_get_filtered_series_metadata_uses_string_language():
    entry = MagicMock()
    entry.id = uuid.uuid4()
    entry.title = "Title"
    entry.description = None
    entry.language = "EN"

    row = MagicMock()
    row.id = uuid.uuid4()
    row.metadata_entries = [entry]
    row.image = None
    row.author_id = uuid.uuid4()
    row.featured = False
    row.status = PlanStatus.DRAFT
    row.plans = None

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.series.series_service.get_series_paginated",
        return_value=([(row, 0)], 1),
    ):
        _session_local_context(mock_session_local)

        result = get_filtered_series(search=None, skip=0, limit=10)

    assert result.series[0].metadata[0].language == "EN"


def test_validate_plan_ids_noop_when_empty():
    with patch("pecha_api.plans.series.series_service.get_plans_by_ids") as mock_get_plans:
        _validate_plan_ids(
            db=MagicMock(),
            plan_ids=[],
            current_author_id=uuid.uuid4(),
            is_admin=False,
        )
    mock_get_plans.assert_not_called()

# ---------------------------------------------------------------------------
# _build_plan_order_pairs: per-language display_order computation
# ---------------------------------------------------------------------------

def test_build_plan_order_pairs_none_returns_empty():
    assert _build_plan_order_pairs(None) == []


def test_build_plan_order_pairs_empty_dict_returns_empty():
    assert _build_plan_order_pairs({}) == []


def test_build_plan_order_pairs_single_language_indexes_from_zero():
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

    pairs = _build_plan_order_pairs({"EN": [a, b, c]})

    assert pairs == [(a, 0), (b, 1), (c, 2)]


def test_build_plan_order_pairs_each_language_numbered_independently():
    a, b, x, y = uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

    pairs = _build_plan_order_pairs({"EN": [a, b], "BO": [x, y]})

    assert pairs == [(a, 0), (b, 1), (x, 0), (y, 1)]


def test_build_plan_order_pairs_preserves_request_order_not_sorted():
    c, a, b = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

    pairs = _build_plan_order_pairs({"EN": [c, a, b]})

    assert pairs == [(c, 0), (a, 1), (b, 2)]


def test_build_plan_order_pairs_dedupes_keeping_first_occurrence():
    a, b = uuid.uuid4(), uuid.uuid4()

    pairs = _build_plan_order_pairs({"EN": [a, a, b]})

    assert pairs == [(a, 0), (b, 1)]


def test_build_plan_order_pairs_handles_more_than_ten_plans():
    ids = [uuid.uuid4() for _ in range(15)]

    pairs = _build_plan_order_pairs({"EN": ids})

    # display_order is a plain counter; it scales past single digits.
    assert pairs == [(pid, idx) for idx, pid in enumerate(ids)]
    assert pairs[-1][1] == 14


def test_build_plan_order_pairs_skips_empty_language_list():
    a = uuid.uuid4()

    pairs = _build_plan_order_pairs({"EN": [a], "BO": []})

    assert pairs == [(a, 0)]


# ---------------------------------------------------------------------------
# PUT: pure reorder of already-attached plans (no add/remove)
# ---------------------------------------------------------------------------

def test_update_existing_series_pure_reorder_sends_all_plans_with_new_order():
    """Reordering already-attached plans (no additions, no removals) must still
    send every plan to the repository so their display_order is rewritten."""
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()

    plan_a_id = uuid.uuid4()
    plan_b_id = uuid.uuid4()
    plan_c_id = uuid.uuid4()

    existing_a = MagicMock()
    existing_a.id = plan_a_id
    existing_a.deleted_at = None
    existing_b = MagicMock()
    existing_b.id = plan_b_id
    existing_b.deleted_at = None
    existing_c = MagicMock()
    existing_c.id = plan_c_id
    existing_c.deleted_at = None

    existing = _make_existing_series(
        series_id, author_id, plans=[existing_a, existing_b, existing_c]
    )
    refreshed = _make_refreshed_series(series_id, author_id)
    mock_author = _make_mock_author(author_id)

    fetched_a = MagicMock()
    fetched_a.id = plan_a_id
    fetched_a.deleted_at = None
    fetched_a.series_id = series_id
    fetched_a.author_id = author_id
    fetched_b = MagicMock()
    fetched_b.id = plan_b_id
    fetched_b.deleted_at = None
    fetched_b.series_id = series_id
    fetched_b.author_id = author_id
    fetched_c = MagicMock()
    fetched_c.id = plan_c_id
    fetched_c.deleted_at = None
    fetched_c.series_id = series_id
    fetched_c.author_id = author_id

    # Same three plans, reordered to C, A, B.
    request = UpdateSeriesRequest(plans={"EN": [plan_c_id, plan_a_id, plan_b_id]})

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", side_effect=[existing, refreshed]), \
         patch("pecha_api.plans.series.series_service.get_plans_by_ids", return_value=[fetched_a, fetched_b, fetched_c]), \
         patch("pecha_api.plans.series.series_service.update_series_with_plans") as mock_update:
        _session_local_context(mock_session_local)
        update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    call_kwargs = mock_update.call_args.kwargs
    assert call_kwargs["plans_to_attach"] == [
        (plan_c_id, 0),
        (plan_a_id, 1),
        (plan_b_id, 2),
    ]
    assert call_kwargs["plan_ids_to_detach"] == []


def test_update_existing_series_multi_language_independent_ordering():
    """Each language list is numbered independently from zero."""
    series_id = uuid.uuid4()
    author_id = uuid.uuid4()

    en_1, en_2 = uuid.uuid4(), uuid.uuid4()
    bo_1, bo_2 = uuid.uuid4(), uuid.uuid4()

    existing = _make_existing_series(series_id, author_id, plans=[])
    refreshed = _make_refreshed_series(series_id, author_id)
    mock_author = _make_mock_author(author_id)

    def _fetched(pid):
        m = MagicMock()
        m.id = pid
        m.deleted_at = None
        m.series_id = None
        m.author_id = author_id
        return m

    request = UpdateSeriesRequest(
        plans={"EN": [en_1, en_2], "BO": [bo_1, bo_2]}
    )

    with patch("pecha_api.plans.series.series_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.series.series_service.validate_and_extract_author_details", return_value=mock_author), \
         patch("pecha_api.plans.series.series_service.get_series_by_id", side_effect=[existing, refreshed]), \
         patch("pecha_api.plans.series.series_service.get_plans_by_ids", return_value=[_fetched(en_1), _fetched(en_2), _fetched(bo_1), _fetched(bo_2)]), \
         patch("pecha_api.plans.series.series_service.update_series_with_plans") as mock_update:
        _session_local_context(mock_session_local)
        update_existing_series(token="dummy", series_id=series_id, update_series_request=request)

    plans_to_attach = mock_update.call_args.kwargs["plans_to_attach"]
    assert plans_to_attach == [(en_1, 0), (en_2, 1), (bo_1, 0), (bo_2, 1)]