from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from pecha_api.region_restrictions.region_restriction_admin_service import (
    create_admin_china_restricted_item,
    delete_admin_china_restricted_item,
    list_admin_china_restricted_items,
    search_admin_china_restriction_candidates,
)
from pecha_api.region_restrictions.region_restriction_enums import RestrictedItemType
from pecha_api.region_restrictions.region_restriction_response_models import (
    ChinaRestrictionCandidateDTO,
    CreateChinaRestrictedItemRequest,
)


def _author():
    return SimpleNamespace(id=uuid4(), email="admin@example.com")


def _row(*, item_type=RestrictedItemType.PLAN, item_id=None, title_time=None):
    now = title_time or datetime(2026, 7, 1, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        item_type=item_type,
        item_id=item_id or uuid4(),
        created_at=now,
        updated_at=now,
    )


@patch("pecha_api.region_restrictions.region_restriction_admin_service.resolve_titles_for_rows")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.list_china_restricted_items")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.SessionLocal")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.require_super_admin_or_reviewer")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.validate_and_extract_author_details")
def test_list_admin_china_restricted_items_enriches_titles(
    mock_validate,
    mock_require,
    mock_session_local,
    mock_list,
    mock_titles,
):
    author = _author()
    mock_validate.return_value = author
    row = _row(item_id=uuid4())
    mock_list.return_value = ([row], 1)
    mock_titles.return_value = {row.item_id: "Morning Practice"}
    db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = db

    result = list_admin_china_restricted_items(
        token="token",
        skip=0,
        limit=20,
        item_type=RestrictedItemType.PLAN,
    )

    mock_require.assert_called_once_with(author)
    mock_list.assert_called_once_with(
        db=db, skip=0, limit=20, item_type=RestrictedItemType.PLAN
    )
    assert result.total == 1
    assert result.items[0].title == "Morning Practice"
    assert result.items[0].item_id == row.item_id


@patch("pecha_api.region_restrictions.region_restriction_admin_service.search_restriction_candidates")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.SessionLocal")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.require_super_admin_or_reviewer")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.validate_and_extract_author_details")
def test_search_admin_china_restriction_candidates(
    mock_validate,
    mock_require,
    mock_session_local,
    mock_search,
):
    mock_validate.return_value = _author()
    candidate = ChinaRestrictionCandidateDTO(id=uuid4(), title="Heart Sutra")
    mock_search.return_value = ([candidate], 1)
    db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = db

    result = search_admin_china_restriction_candidates(
        token="token",
        item_type=RestrictedItemType.RECITATION,
        search="heart",
        skip=0,
        limit=10,
    )

    mock_search.assert_called_once_with(
        db=db,
        item_type=RestrictedItemType.RECITATION,
        search="heart",
        skip=0,
        limit=10,
    )
    assert result.total == 1
    assert result.items[0].title == "Heart Sutra"


@patch("pecha_api.region_restrictions.region_restriction_admin_service.clear_restricted_items_cache")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.resolve_titles_for_rows")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.create_china_restricted_item")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.is_item_restricted_in_china")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.SessionLocal")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.require_super_admin")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.validate_and_extract_author_details")
def test_create_admin_china_restricted_item_success(
    mock_validate,
    mock_require,
    mock_session_local,
    mock_is_restricted,
    mock_create,
    mock_titles,
    mock_clear_cache,
):
    author = _author()
    mock_validate.return_value = author
    mock_is_restricted.return_value = False
    item_id = uuid4()
    row = _row(item_type=RestrictedItemType.SERIES, item_id=item_id)
    mock_create.return_value = row
    mock_titles.return_value = {item_id: "Series Title"}
    db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = db
    body = CreateChinaRestrictedItemRequest(
        item_type=RestrictedItemType.SERIES,
        item_id=item_id,
    )

    result = create_admin_china_restricted_item(token="token", body=body)

    mock_require.assert_called_once_with(author)
    mock_create.assert_called_once_with(
        db=db, item_type=RestrictedItemType.SERIES, item_id=item_id
    )
    mock_clear_cache.assert_called_once()
    assert result.title == "Series Title"
    assert result.item_id == item_id


@patch("pecha_api.region_restrictions.region_restriction_admin_service.is_item_restricted_in_china")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.SessionLocal")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.require_super_admin")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.validate_and_extract_author_details")
def test_create_admin_china_restricted_item_conflict(
    mock_validate,
    mock_require,
    mock_session_local,
    mock_is_restricted,
):
    mock_validate.return_value = _author()
    mock_is_restricted.return_value = True
    mock_session_local.return_value.__enter__.return_value = MagicMock()
    body = CreateChinaRestrictedItemRequest(
        item_type=RestrictedItemType.PLAN,
        item_id=uuid4(),
    )

    with pytest.raises(HTTPException) as exc_info:
        create_admin_china_restricted_item(token="token", body=body)

    assert exc_info.value.status_code == 409


@patch("pecha_api.region_restrictions.region_restriction_admin_service.clear_restricted_items_cache")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.delete_china_restricted_item_by_id")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.SessionLocal")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.require_super_admin")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.validate_and_extract_author_details")
def test_delete_admin_china_restricted_item_success(
    mock_validate,
    mock_require,
    mock_session_local,
    mock_delete,
    mock_clear_cache,
):
    mock_validate.return_value = _author()
    mock_delete.return_value = True
    mock_session_local.return_value.__enter__.return_value = MagicMock()
    row_id = uuid4()

    delete_admin_china_restricted_item(token="token", row_id=row_id)

    mock_delete.assert_called_once()
    mock_clear_cache.assert_called_once()


@patch("pecha_api.region_restrictions.region_restriction_admin_service.delete_china_restricted_item_by_id")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.SessionLocal")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.require_super_admin")
@patch("pecha_api.region_restrictions.region_restriction_admin_service.validate_and_extract_author_details")
def test_delete_admin_china_restricted_item_not_found(
    mock_validate,
    mock_require,
    mock_session_local,
    mock_delete,
):
    mock_validate.return_value = _author()
    mock_delete.return_value = False
    mock_session_local.return_value.__enter__.return_value = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        delete_admin_china_restricted_item(token="token", row_id=uuid4())

    assert exc_info.value.status_code == 404


def test_row_to_dto_normalizes_string_item_type():
    from pecha_api.region_restrictions.region_restriction_admin_service import _row_to_dto

    row = _row(item_type="PLAN")
    row.updated_at = None
    dto = _row_to_dto(row, title="From string type")
    assert dto.item_type == RestrictedItemType.PLAN
    assert dto.title == "From string type"
    assert dto.updated_at is None
