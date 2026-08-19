from unittest.mock import MagicMock, patch
from uuid import uuid4

from pecha_api.region_restrictions.region_restriction_enums import RestrictedItemType
from pecha_api.region_restrictions.region_restriction_models import ChinaRestrictedItem
from pecha_api.region_restrictions.region_restriction_repository import (
    create_china_restricted_item,
    delete_china_restricted_item_by_id,
    get_all_china_restricted_items,
    is_item_restricted_in_china,
    list_china_restricted_items,
)


def test_get_all_china_restricted_items():
    db = MagicMock()
    rows = [MagicMock(), MagicMock()]
    db.query.return_value.all.return_value = rows

    assert get_all_china_restricted_items(db=db) == rows
    db.query.assert_called_once_with(ChinaRestrictedItem)


def test_list_china_restricted_items_without_type_filter():
    db = MagicMock()
    query = MagicMock()
    db.query.return_value = query
    query.count.return_value = 2
    rows = [MagicMock(), MagicMock()]
    query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = rows

    result_rows, total = list_china_restricted_items(db=db, skip=5, limit=10)

    assert total == 2
    assert result_rows == rows
    query.filter.assert_not_called()
    query.order_by.assert_called_once()
    query.order_by.return_value.offset.assert_called_once_with(5)
    query.order_by.return_value.offset.return_value.limit.assert_called_once_with(10)


def test_list_china_restricted_items_with_type_filter():
    db = MagicMock()
    query = MagicMock()
    filtered = MagicMock()
    db.query.return_value = query
    query.filter.return_value = filtered
    filtered.count.return_value = 1
    filtered.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
        MagicMock()
    ]

    rows, total = list_china_restricted_items(
        db=db, skip=0, limit=20, item_type=RestrictedItemType.MANTRA
    )

    assert total == 1
    assert len(rows) == 1
    query.filter.assert_called_once()


def test_create_china_restricted_item():
    db = MagicMock()
    item_id = uuid4()
    created = MagicMock()
    created.item_type = RestrictedItemType.PLAN
    created.item_id = item_id

    with patch(
        "pecha_api.region_restrictions.region_restriction_repository.ChinaRestrictedItem",
        return_value=created,
    ) as mock_model:
        row = create_china_restricted_item(
            db=db,
            item_type=RestrictedItemType.PLAN,
            item_id=item_id,
        )

    mock_model.assert_called_once_with(
        item_type=RestrictedItemType.PLAN, item_id=item_id
    )
    db.add.assert_called_once_with(created)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(created)
    assert row is created


def test_delete_china_restricted_item_by_id_success():
    db = MagicMock()
    row = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = row

    assert delete_china_restricted_item_by_id(db=db, row_id=uuid4()) is True
    db.delete.assert_called_once_with(row)
    db.commit.assert_called_once()


def test_delete_china_restricted_item_by_id_missing():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    assert delete_china_restricted_item_by_id(db=db, row_id=uuid4()) is False
    db.delete.assert_not_called()
    db.commit.assert_not_called()


def test_is_item_restricted_in_china_true():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = (uuid4(),)

    assert (
        is_item_restricted_in_china(
            db=db, item_type=RestrictedItemType.GROUP, item_id=uuid4()
        )
        is True
    )


def test_is_item_restricted_in_china_false():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    assert (
        is_item_restricted_in_china(
            db=db, item_type=RestrictedItemType.GROUP, item_id=uuid4()
        )
        is False
    )
