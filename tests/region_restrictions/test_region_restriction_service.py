from unittest.mock import patch
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


def test_filter_items_for_timezone_hides_restricted_items_in_china():
    visible_id = uuid4()
    hidden_id = uuid4()
    items = [{"id": visible_id}, {"id": hidden_id}]

    with patch(
        "pecha_api.region_restrictions.region_restriction_service.get_restricted_item_ids",
        return_value=frozenset({hidden_id}),
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
