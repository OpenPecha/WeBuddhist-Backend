from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from pecha_api.region_restrictions.china_timezone import (
    get_chinese_timezone_ids,
    is_china_timezone,
)
from pecha_api.region_restrictions.region_restriction_enums import RestrictedItemType
from pecha_api.region_restrictions.region_restriction_service import (
    assert_visible_for_timezone,
    clear_restricted_items_cache,
    filter_items_for_timezone,
    get_restricted_item_ids,
    is_restricted_in_china,
    should_hide_for_timezone,
)


@pytest.fixture(autouse=True)
def clear_cache():
    get_chinese_timezone_ids.cache_clear()
    clear_restricted_items_cache()
    yield
    get_chinese_timezone_ids.cache_clear()
    clear_restricted_items_cache()


def test_is_china_timezone_matches_configured_ids():
    assert is_china_timezone("Asia/Shanghai") is True
    assert is_china_timezone("Asia/Hong_Kong") is True
    assert is_china_timezone("America/Los_Angeles") is False
    assert is_china_timezone(None) is False
    assert is_china_timezone("") is False
    assert is_china_timezone("   ") is False
    assert is_china_timezone(" Asia/Shanghai ") is True


def test_filter_items_for_timezone_hides_restricted_items_in_china():
    visible_id = uuid4()
    hidden_id = uuid4()
    items = [{"id": visible_id}, {"id": hidden_id}]

    with patch(
        "pecha_api.region_restrictions.region_restriction_service.get_restricted_item_ids",
        return_value=frozenset({str(hidden_id)}),
    ):
        filtered = filter_items_for_timezone(
            items,
            timezone_name="Asia/Shanghai",
            item_type=RestrictedItemType.MANTRA,
            id_of=lambda item: item["id"],
        )

    assert filtered == [{"id": visible_id}]


def test_filter_items_for_timezone_keeps_all_items_outside_china():
    hidden_id = uuid4()
    items = [{"id": hidden_id}]

    with patch(
        "pecha_api.region_restrictions.region_restriction_service.get_restricted_item_ids",
        return_value=frozenset({hidden_id}),
    ):
        filtered = filter_items_for_timezone(
            items,
            timezone_name="America/Los_Angeles",
            item_type=RestrictedItemType.MANTRA,
            id_of=lambda item: item["id"],
        )

    assert filtered == items


def test_filter_items_for_timezone_keeps_all_when_no_restricted_ids():
    items = [{"id": uuid4()}, {"id": uuid4()}]

    with patch(
        "pecha_api.region_restrictions.region_restriction_service.get_restricted_item_ids",
        return_value=frozenset(),
    ):
        filtered = filter_items_for_timezone(
            items,
            timezone_name="Asia/Shanghai",
            item_type=RestrictedItemType.PLAN,
            id_of=lambda item: item["id"],
        )

    assert filtered == items


def test_should_hide_for_timezone():
    item_id = uuid4()

    with patch(
        "pecha_api.region_restrictions.region_restriction_service.is_restricted_in_china",
        return_value=True,
    ):
        assert should_hide_for_timezone("Asia/Shanghai", RestrictedItemType.PLAN, item_id) is True
        assert should_hide_for_timezone("America/New_York", RestrictedItemType.PLAN, item_id) is False


def test_assert_visible_for_timezone_raises_for_restricted_item():
    item_id = uuid4()

    with patch(
        "pecha_api.region_restrictions.region_restriction_service.should_hide_for_timezone",
        return_value=True,
    ):
        with pytest.raises(HTTPException) as exc_info:
            assert_visible_for_timezone(
                timezone_name="Asia/Shanghai",
                item_type=RestrictedItemType.MANTRA,
                item_id=item_id,
                not_found_detail="Not found",
            )

    assert exc_info.value.status_code == 404


def test_assert_visible_for_timezone_allows_visible_item():
    item_id = uuid4()

    with patch(
        "pecha_api.region_restrictions.region_restriction_service.should_hide_for_timezone",
        return_value=False,
    ):
        assert_visible_for_timezone(
            timezone_name="Asia/Shanghai",
            item_type=RestrictedItemType.MANTRA,
            item_id=item_id,
        )


def test_get_restricted_item_ids_and_is_restricted_in_china():
    item_id = uuid4()
    other_id = uuid4()

    with patch(
        "pecha_api.region_restrictions.region_restriction_service._load_restricted_item_ids_by_type",
        return_value={RestrictedItemType.PLAN.value: frozenset({str(item_id)})},
    ):
        assert get_restricted_item_ids(RestrictedItemType.PLAN) == frozenset({str(item_id)})
        assert get_restricted_item_ids(RestrictedItemType.MANTRA) == frozenset()
        assert is_restricted_in_china(RestrictedItemType.PLAN, item_id) is True
        assert is_restricted_in_china(RestrictedItemType.PLAN, other_id) is False


def test_load_restricted_item_ids_by_type_groups_rows():
    plan_id = uuid4()
    mantra_id = uuid4()
    rows = [
        MagicMock(item_type=RestrictedItemType.PLAN, item_id=plan_id),
        MagicMock(item_type="MANTRA", item_id=mantra_id),
    ]

    with patch(
        "pecha_api.region_restrictions.region_restriction_service.SessionLocal"
    ) as mock_session_local, patch(
        "pecha_api.region_restrictions.region_restriction_service.get_all_china_restricted_items",
        return_value=rows,
    ):
        mock_session_local.return_value.__enter__.return_value = MagicMock()
        clear_restricted_items_cache()
        assert get_restricted_item_ids(RestrictedItemType.PLAN) == frozenset({str(plan_id)})
        assert get_restricted_item_ids(RestrictedItemType.MANTRA) == frozenset({str(mantra_id)})
