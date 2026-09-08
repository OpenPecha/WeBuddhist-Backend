import uuid
from unittest.mock import patch

from pecha_api.region_restrictions.region_restriction_enums import RestrictedItemType
from pecha_api.region_restrictions.region_restriction_response_models import (
    ChinaRestrictedItemDTO,
    ChinaRestrictedItemListResponse,
    ChinaRestrictionCandidateDTO,
    ChinaRestrictionCandidateListResponse,
    CreateChinaRestrictedItemRequest,
)
from pecha_api.region_restrictions.region_restriction_views import (
    delete_cms_china_restricted_item,
    get_cms_china_restriction_candidates,
    get_cms_china_restricted_items,
    post_cms_china_restricted_item,
)


def test_get_cms_china_restricted_items_delegates_to_service():
    expected = ChinaRestrictedItemListResponse(items=[], skip=0, limit=20, total=0)

    with patch(
        "pecha_api.region_restrictions.region_restriction_views.list_admin_china_restricted_items",
        return_value=expected,
    ) as mock_service:
        resp = get_cms_china_restricted_items(
            skip=0,
            limit=20,
            item_type=None,
            token="token123",
        )

    assert resp == expected
    mock_service.assert_called_once_with(
        token="token123",
        skip=0,
        limit=20,
        item_type=None,
    )


def test_get_cms_china_restriction_candidates_delegates_to_service():
    expected = ChinaRestrictionCandidateListResponse(
        items=[
            ChinaRestrictionCandidateDTO(
                id=str(uuid.uuid4()),
                title="Morning Practice",
            )
        ],
        skip=0,
        limit=20,
        total=1,
    )

    with patch(
        "pecha_api.region_restrictions.region_restriction_views.search_admin_china_restriction_candidates",
        return_value=expected,
    ) as mock_service:
        resp = get_cms_china_restriction_candidates(
            item_type=RestrictedItemType.PLAN,
            search="morning",
            skip=0,
            limit=20,
            token="token123",
        )

    assert resp == expected
    mock_service.assert_called_once_with(
        token="token123",
        item_type=RestrictedItemType.PLAN,
        search="morning",
        skip=0,
        limit=20,
    )


def test_post_cms_china_restricted_item_delegates_to_service():
    item_id = str(uuid.uuid4())
    row_id = uuid.uuid4()
    body = CreateChinaRestrictedItemRequest(
        item_type=RestrictedItemType.PLAN,
        item_id=item_id,
    )
    expected = ChinaRestrictedItemDTO(
        id=row_id,
        item_type=RestrictedItemType.PLAN,
        item_id=item_id,
        title="Morning Practice",
        created_at="2026-07-05T00:00:00+00:00",
    )

    with patch(
        "pecha_api.region_restrictions.region_restriction_views.create_admin_china_restricted_item",
        return_value=expected,
    ) as mock_service:
        resp = post_cms_china_restricted_item(body=body, token="token123")

    assert resp == expected
    mock_service.assert_called_once_with(token="token123", body=body)


def test_delete_cms_china_restricted_item_delegates_to_service():
    row_id = uuid.uuid4()

    with patch(
        "pecha_api.region_restrictions.region_restriction_views.delete_admin_china_restricted_item",
    ) as mock_service:
        delete_cms_china_restricted_item(row_id=row_id, token="token123")

    mock_service.assert_called_once_with(token="token123", row_id=row_id)
