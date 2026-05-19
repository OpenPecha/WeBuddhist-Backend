import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pecha_api.plans.series.series_model import Series
from pecha_api.plans.series.series_repository import get_series_by_id, get_series_paginated, save_series_with_plans


def _make_session_mock() -> Session:
    return MagicMock(spec=Session)


def _paginated_query_chain(rows, total, *, with_filter=True):
    query_mock = MagicMock()
    options_mock = MagicMock()
    target = options_mock.filter.return_value if with_filter else options_mock
    target.count.return_value = total
    ordered = MagicMock()
    ordered.offset.return_value.limit.return_value.all.return_value = rows
    target.order_by.return_value = ordered
    query_mock.options.return_value = options_mock
    return query_mock


def test_save_series_success_commits_and_returns_series():
    db = _make_session_mock()
    series = MagicMock(name="SeriesInstance")

    result = save_series_with_plans(db=db, series=series, metadata_entries=[], plan_ids=None)

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
        save_series_with_plans(db=db, series=series, metadata_entries=[], plan_ids=None)


def test_get_series_paginated_no_search_returns_rows_and_total():
    db = _make_session_mock()
    row1 = MagicMock(spec=Series)
    row2 = MagicMock(spec=Series)

    db.query.return_value = _paginated_query_chain([row1, row2], 2)

    rows, total = get_series_paginated(db=db, search=None, skip=0, limit=10)

    assert total == 2
    assert rows == [row1, row2]
    db.query.assert_called_once_with(Series)
    db.query.return_value.options.return_value.filter.return_value.count.assert_called_once()
    db.query.return_value.options.return_value.filter.return_value.order_by.assert_called_once()


def test_get_series_paginated_with_include_deleted():
    db = _make_session_mock()
    row = MagicMock(spec=Series)

    db.query.return_value = _paginated_query_chain([row], 1, with_filter=False)

    rows, total = get_series_paginated(
        db=db, search=None, skip=0, limit=10, include_deleted=True
    )

    assert total == 1
    assert rows == [row]
    db.query.return_value.options.return_value.filter.assert_not_called()


def test_get_series_paginated_with_custom_ordering():
    db = _make_session_mock()
    row = MagicMock(spec=Series)

    db.query.return_value = _paginated_query_chain([row], 1)

    rows, total = get_series_paginated(
        db=db,
        search=None,
        skip=0,
        limit=10,
        order_by_field=Series.created_at,
        order_desc=False,
    )

    assert total == 1
    assert rows == [row]
    db.query.return_value.options.return_value.filter.return_value.order_by.assert_called_once()


def test_get_series_paginated_with_search_applies_filter_and_pagination():
    db = _make_session_mock()

    db.query.return_value = _paginated_query_chain([], 0)

    rows, total = get_series_paginated(db=db, search="meditation", skip=5, limit=20)

    assert rows == []
    assert total == 0
    filtered = db.query.return_value.options.return_value.filter
    assert filtered.call_count == 1
    filter_args = filtered.call_args[0]
    assert len(filter_args) == 2
    filtered.return_value.order_by.assert_called_once()
    filtered.return_value.order_by.return_value.offset.assert_called_once_with(5)
    filtered.return_value.order_by.return_value.offset.return_value.limit.assert_called_once_with(20)


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
