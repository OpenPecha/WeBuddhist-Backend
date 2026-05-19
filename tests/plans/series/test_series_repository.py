import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pecha_api.plans.series.series_model import Series
from pecha_api.plans.series.series_repository import get_series_by_id, get_series_paginated, save_series_with_plans


def _make_session_mock() -> Session:
    return MagicMock(spec=Session)


def test_save_series_success_commits_and_returns_series():
    db = _make_session_mock()
    series = MagicMock(name="SeriesInstance")

    result = save_series_with_plans(db=db, series=series, plan_ids=None)

    assert result is series
    db.add.assert_called_once_with(series)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(series)


def test_save_series_integrity_error_propagates():
    db = _make_session_mock()
    series = MagicMock(name="SeriesInstance")
    orig = Exception("foreign key violation")
    db.commit.side_effect = IntegrityError("statement", {}, orig)

    with pytest.raises(IntegrityError):
        save_series_with_plans(db=db, series=series, plan_ids=None)


def test_get_series_paginated_no_search_returns_rows_and_total():
    db = _make_session_mock()
    row1 = MagicMock(spec=Series)
    row2 = MagicMock(spec=Series)
    
    query_mock = MagicMock()
    filtered = MagicMock()
    filtered.count.return_value = 2
    ordered = MagicMock()
    ordered.offset.return_value.limit.return_value.all.return_value = [row1, row2]
    filtered.order_by.return_value = ordered
    query_mock.filter.return_value = filtered
    db.query.return_value = query_mock

    rows, total = get_series_paginated(db=db, search=None, skip=0, limit=10)

    assert total == 2
    assert rows == [row1, row2]
    db.query.assert_called_once_with(Series)
    filtered.count.assert_called_once()
    filtered.order_by.assert_called_once()
    ordered.offset.assert_called_once_with(0)
    ordered.offset.return_value.limit.assert_called_once_with(10)


def test_get_series_paginated_with_include_deleted():
    db = _make_session_mock()
    row = MagicMock(spec=Series)
    
    query_mock = MagicMock()
    query_mock.count.return_value = 1
    ordered = MagicMock()
    ordered.offset.return_value.limit.return_value.all.return_value = [row]
    query_mock.order_by.return_value = ordered
    db.query.return_value = query_mock

    rows, total = get_series_paginated(
        db=db, search=None, skip=0, limit=10, include_deleted=True
    )

    assert total == 1
    assert rows == [row]
    # When include_deleted=True, no filter should be applied for deleted_at
    query_mock.filter.assert_not_called()


def test_get_series_paginated_with_custom_ordering():
    db = _make_session_mock()
    row = MagicMock(spec=Series)
    
    query_mock = MagicMock()
    filtered = MagicMock()
    filtered.count.return_value = 1
    ordered = MagicMock()
    ordered.offset.return_value.limit.return_value.all.return_value = [row]
    filtered.order_by.return_value = ordered
    query_mock.filter.return_value = filtered
    db.query.return_value = query_mock

    rows, total = get_series_paginated(
        db=db,
        search=None,
        skip=0,
        limit=10,
        order_by_field=Series.name,
        order_desc=False,
    )

    assert total == 1
    assert rows == [row]
    filtered.order_by.assert_called_once()


def test_get_series_paginated_with_search_applies_filter_and_pagination():
    db = _make_session_mock()
    filtered_after_search = MagicMock()
    filtered_after_search.count.return_value = 0
    ordered = MagicMock()
    ordered.offset.return_value.limit.return_value.all.return_value = []
    filtered_after_search.order_by.return_value = ordered

    base_query = MagicMock()
    base_query.filter.return_value = filtered_after_search
    db.query.return_value = base_query

    rows, total = get_series_paginated(db=db, search="meditation", skip=5, limit=20)

    assert rows == []
    assert total == 0
    assert base_query.filter.call_count == 1
    filter_args = base_query.filter.call_args[0]
    assert len(filter_args) == 2
    filtered_after_search.order_by.assert_called_once()
    ordered.offset.assert_called_once_with(5)
    ordered.offset.return_value.limit.assert_called_once_with(20)


def test_get_series_by_id_returns_series_when_found():
    db = _make_session_mock()
    series_id = uuid.uuid4()
    row = MagicMock(spec=Series)
    filtered = MagicMock()
    filtered.first.return_value = row
    query_chain = MagicMock()
    query_chain.options.return_value.filter.return_value = filtered
    db.query.return_value = query_chain

    result = get_series_by_id(db=db, series_id=series_id)

    assert result is row
    db.query.assert_called_once_with(Series)
    query_chain.options.assert_called_once()
    query_chain.options.return_value.filter.assert_called_once()


def test_get_series_by_id_returns_none_when_missing():
    db = _make_session_mock()
    series_id = uuid.uuid4()
    filtered = MagicMock()
    filtered.first.return_value = None
    query_chain = MagicMock()
    query_chain.options.return_value.filter.return_value = filtered
    db.query.return_value = query_chain

    result = get_series_by_id(db=db, series_id=series_id)

    assert result is None
