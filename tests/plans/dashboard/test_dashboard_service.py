import json
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from pecha_api.plans.dashboard.dashboard_service import (
    get_dashboard_items_list,
    get_practice_items_list,
)
from pecha_api.plans.media.media_response_models import ImageUrlModel
from pecha_api.plans.plans_enums import PlanStatus


def _session_local_context(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_session_local.return_value.__exit__.return_value = False
    return mock_db


def _make_mock_author(*, author_id=None, is_admin=False):
    author = MagicMock()
    author.id = author_id or uuid.uuid4()
    author.is_admin = is_admin
    return author


def _make_series_row(**overrides):
    meta_id = uuid.uuid4()
    row_id = uuid.uuid4()
    author_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    defaults = {
        "item_type": "series",
        "id": row_id,
        "image_key": "series/cover.jpg",
        "status": PlanStatus.DRAFT,
        "featured": True,
        "languages_raw": "EN, BO",
        "enrolled_count": 3,
        "plans_count": 2,
        "updated_at": now,
        "created_at": now,
        "metadata_json": [
            {
                "id": str(meta_id),
                "title": "Foundations",
                "description": "Intro",
                "language": "EN",
            }
        ],
        "author_id": author_id,
        "title": None,
    }
    defaults.update(overrides)
    row = MagicMock()
    for key, value in defaults.items():
        setattr(row, key, value)
    return row


def _make_plan_row(**overrides):
    now = datetime.now(timezone.utc)
    defaults = {
        "item_type": "plan",
        "id": uuid.uuid4(),
        "image_key": None,
        "status": PlanStatus.DRAFT.value,
        "featured": False,
        "languages_raw": "EN",
        "enrolled_count": 10,
        "plans_count": None,
        "updated_at": now,
        "created_at": now,
        "metadata_json": None,
        "author_id": None,
        "title": "Standalone plan",
    }
    defaults.update(overrides)
    row = MagicMock()
    for key, value in defaults.items():
        setattr(row, key, value)
    return row


def test_get_dashboard_items_list_admin_passes_no_author_filter():
    mock_admin = _make_mock_author(is_admin=True)
    series_row = _make_series_row()

    with patch(
        "pecha_api.plans.dashboard.dashboard_service.validate_and_extract_author_details",
        return_value=mock_admin,
    ), patch(
        "pecha_api.plans.dashboard.dashboard_service.SessionLocal"
    ) as mock_session_local, patch(
        "pecha_api.plans.dashboard.dashboard_service.get_dashboard_items",
        return_value=([series_row], 1),
    ) as mock_repo, patch(
        "pecha_api.plans.dashboard.dashboard_service.safe_get_image_url",
        return_value=ImageUrlModel(
            thumbnail="https://signed.example/cover-thumb.jpg",
            medium="https://signed.example/cover-medium.jpg",
            original="https://signed.example/cover.jpg",
        ),
    ):
        _session_local_context(mock_session_local)
        result = get_dashboard_items_list(
            token="admin-token",
            tab="all",
            page=1,
            page_size=20,
        )

    assert mock_repo.call_args.kwargs["author_id"] is None
    assert len(result.items) == 1
    assert result.items[0].type == "series"
    assert result.items[0].author_id == series_row.author_id
    assert len(result.items[0].metadata) == 1
    assert result.items[0].metadata[0].title == "Foundations"
    assert result.items[0].languages == ["EN", "BO"]
    assert result.items[0].image is not None
    assert result.items[0].image.original == "https://signed.example/cover.jpg"
    assert result.items[0].plans_count == 2
    assert result.pagination.total == 1
    assert result.pagination.total_pages == 1


def test_get_dashboard_items_list_non_admin_scopes_to_author():
    author_id = uuid.uuid4()
    mock_author = _make_mock_author(author_id=author_id, is_admin=False)

    with patch(
        "pecha_api.plans.dashboard.dashboard_service.validate_and_extract_author_details",
        return_value=mock_author,
    ), patch(
        "pecha_api.plans.dashboard.dashboard_service.SessionLocal"
    ) as mock_session_local, patch(
        "pecha_api.plans.dashboard.dashboard_service.get_dashboard_items",
        return_value=([], 0),
    ) as mock_repo:
        _session_local_context(mock_session_local)
        get_dashboard_items_list(
            token="author-token",
            tab="series",
            page=1,
            page_size=10,
            search="found",
            status=PlanStatus.PUBLISHED,
            language="en",
            featured=False,
        )

    mock_repo.assert_called_once()
    kwargs = mock_repo.call_args.kwargs
    assert kwargs["author_id"] == author_id
    assert kwargs["tab"] == "series"
    assert kwargs["search"] == "found"
    assert kwargs["status"] == PlanStatus.PUBLISHED
    assert kwargs["language"] == "en"
    assert kwargs["featured"] is False


def test_get_dashboard_items_list_clamps_page_and_page_size():
    mock_author = _make_mock_author(is_admin=True)

    with patch(
        "pecha_api.plans.dashboard.dashboard_service.validate_and_extract_author_details",
        return_value=mock_author,
    ), patch(
        "pecha_api.plans.dashboard.dashboard_service.SessionLocal"
    ) as mock_session_local, patch(
        "pecha_api.plans.dashboard.dashboard_service.get_dashboard_items",
        return_value=([], 0),
    ) as mock_repo:
        _session_local_context(mock_session_local)
        result = get_dashboard_items_list(
            token="token",
            tab="plans",
            page=0,
            page_size=-5,
        )

    assert mock_repo.call_args.kwargs["page"] == 1
    assert mock_repo.call_args.kwargs["page_size"] == 1
    assert result.pagination.page == 1
    assert result.pagination.page_size == 1
    assert result.pagination.total_pages == 0


def test_get_dashboard_items_list_maps_plan_row():
    plan_row = _make_plan_row()

    with patch(
        "pecha_api.plans.dashboard.dashboard_service.validate_and_extract_author_details",
        return_value=_make_mock_author(is_admin=True),
    ), patch(
        "pecha_api.plans.dashboard.dashboard_service.SessionLocal"
    ) as mock_session_local, patch(
        "pecha_api.plans.dashboard.dashboard_service.get_dashboard_items",
        return_value=([plan_row], 1),
    ):
        _session_local_context(mock_session_local)
        result = get_dashboard_items_list(
            token="token",
            tab="plans",
            page=1,
            page_size=20,
        )

    item = result.items[0]
    assert item.type == "plan"
    assert item.title == "Standalone plan"
    assert item.metadata is None
    assert item.author_id is None
    assert item.languages == ["EN"]
    assert item.image is None
    assert item.plans_count is None
    assert item.status == PlanStatus.DRAFT
    assert item.enrolled_count == 10


def test_get_dashboard_items_list_parses_metadata_json_string():
    meta_id = uuid.uuid4()
    series_row = _make_series_row(
        image_key=None,
        metadata_json=json.dumps(
            [
                {
                    "id": str(meta_id),
                    "title": "From JSON",
                    "description": None,
                    "language": "BO",
                }
            ]
        ),
        languages_raw=None,
        enrolled_count=None,
    )

    with patch(
        "pecha_api.plans.dashboard.dashboard_service.validate_and_extract_author_details",
        return_value=_make_mock_author(is_admin=True),
    ), patch(
        "pecha_api.plans.dashboard.dashboard_service.SessionLocal"
    ) as mock_session_local, patch(
        "pecha_api.plans.dashboard.dashboard_service.get_dashboard_items",
        return_value=([series_row], 1),
    ):
        _session_local_context(mock_session_local)
        result = get_dashboard_items_list(
            token="token",
            tab="series",
            page=2,
            page_size=10,
        )

    item = result.items[0]
    assert item.metadata[0].title == "From JSON"
    assert item.metadata[0].language == "BO"
    assert item.languages == []
    assert item.enrolled_count == 0
    assert item.image is None


def test_get_dashboard_items_list_series_with_null_metadata():
    series_row = _make_series_row(metadata_json=None, image_key=None)

    with patch(
        "pecha_api.plans.dashboard.dashboard_service.validate_and_extract_author_details",
        return_value=_make_mock_author(is_admin=True),
    ), patch(
        "pecha_api.plans.dashboard.dashboard_service.SessionLocal"
    ) as mock_session_local, patch(
        "pecha_api.plans.dashboard.dashboard_service.get_dashboard_items",
        return_value=([series_row], 1),
    ):
        _session_local_context(mock_session_local)
        result = get_dashboard_items_list(
            token="token",
            tab="series",
            page=1,
            page_size=20,
        )

    assert result.items[0].metadata == []


def test_get_dashboard_items_list_empty_metadata_and_default_plan_title():
    series_row = _make_series_row(metadata_json=[])
    plan_row = _make_plan_row(title=None)

    with patch(
        "pecha_api.plans.dashboard.dashboard_service.validate_and_extract_author_details",
        return_value=_make_mock_author(is_admin=True),
    ), patch(
        "pecha_api.plans.dashboard.dashboard_service.SessionLocal"
    ) as mock_session_local, patch(
        "pecha_api.plans.dashboard.dashboard_service.get_dashboard_items",
        return_value=([series_row, plan_row], 25),
    ):
        _session_local_context(mock_session_local)
        result = get_dashboard_items_list(
            token="token",
            tab="all",
            page=2,
            page_size=10,
        )

    assert result.items[0].metadata == []
    assert result.items[1].title == ""
    assert result.pagination.total == 25
    assert result.pagination.total_pages == 3


def test_get_practice_items_list_forces_published_and_public_scope():
    series_row = _make_series_row()

    with patch(
        "pecha_api.plans.dashboard.dashboard_service.SessionLocal"
    ) as mock_session_local, patch(
        "pecha_api.plans.dashboard.dashboard_service.get_dashboard_items",
        return_value=([series_row], 1),
    ) as mock_repo, patch(
        "pecha_api.plans.dashboard.dashboard_service._published_plans_by_series",
        return_value={},
    ), patch(
        "pecha_api.plans.dashboard.dashboard_service.safe_get_image_url",
        return_value=ImageUrlModel(
            thumbnail="https://signed.example/cover-thumb.jpg",
            medium="https://signed.example/cover-medium.jpg",
            original="https://signed.example/cover.jpg",
        ),
    ):
        _session_local_context(mock_session_local)
        result = get_practice_items_list(
            tab="series",
            page=1,
            page_size=20,
            search="found",
            language="en",
            featured=True,
        )

    kwargs = mock_repo.call_args.kwargs
    assert kwargs["status"] == PlanStatus.PUBLISHED
    assert kwargs["author_id"] is None
    assert kwargs["tab"] == "series"
    assert kwargs["search"] == "found"
    assert kwargs["language"] == "en"
    assert kwargs["featured"] is True
    assert result.items[0].author_id is None
    assert result.items[0].image is not None
    assert result.items[0].image.original == "https://signed.example/cover.jpg"
    assert result.pagination.total == 1
    assert result.pagination.total_pages == 1


def test_get_practice_items_list_clamps_page_and_page_size():
    with patch(
        "pecha_api.plans.dashboard.dashboard_service.SessionLocal"
    ) as mock_session_local, patch(
        "pecha_api.plans.dashboard.dashboard_service.get_dashboard_items",
        return_value=([], 0),
    ) as mock_repo:
        _session_local_context(mock_session_local)
        result = get_practice_items_list(
            tab="all",
            page=0,
            page_size=-5,
        )

    assert mock_repo.call_args.kwargs["page"] == 1
    assert mock_repo.call_args.kwargs["page_size"] == 1
    assert result.pagination.page == 1
    assert result.pagination.page_size == 1
    assert result.pagination.total_pages == 0
