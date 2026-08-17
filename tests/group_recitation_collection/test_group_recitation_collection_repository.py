from unittest.mock import MagicMock
from uuid import uuid4

from pecha_api.group_recitation_collection.repository import (
    get_collections_for_group_ids_with_total,
)


def test_get_collections_for_group_ids_with_total_empty_group_ids_returns_early():
    db = MagicMock()

    result = get_collections_for_group_ids_with_total(db=db, group_ids=[], limit=20)

    assert result == ([], 0)
    db.query.assert_not_called()


def test_get_collections_for_group_ids_with_total_without_exclude_ids():
    db = MagicMock()
    group_id = uuid4()
    collection = MagicMock()
    query = MagicMock()
    db.query.return_value = query
    query.filter.return_value = query
    query.count.return_value = 1
    query.order_by.return_value = query
    query.limit.return_value = query
    query.limit.return_value.all.return_value = [collection]

    collections, total = get_collections_for_group_ids_with_total(
        db=db, group_ids=[group_id], limit=20
    )

    assert collections == [collection]
    assert total == 1
    query.filter.assert_called_once()


def test_get_collections_for_group_ids_with_total_with_exclude_ids_applies_extra_filter():
    db = MagicMock()
    group_id = uuid4()
    excluded_id = uuid4()
    query = MagicMock()
    db.query.return_value = query
    query.filter.return_value = query
    query.count.return_value = 0
    query.order_by.return_value = query
    query.limit.return_value = query
    query.limit.return_value.all.return_value = []

    get_collections_for_group_ids_with_total(
        db=db, group_ids=[group_id], limit=20, exclude_ids=[excluded_id]
    )

    assert query.filter.call_count == 2
