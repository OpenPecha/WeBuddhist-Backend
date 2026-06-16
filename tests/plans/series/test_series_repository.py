import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pecha_api.plans.plans_enums import PlanStatus
from pecha_api.plans.series.series_model import Series
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.series.series_repository import (
    get_series_by_id,
    get_series_paginated,
    get_random_featured_published_series,
    save_series_with_plans,
    update_series_with_plans,
    update_series_status,
    update_series_featured,
    soft_delete_series_with_plan_detach,
)


def _make_session_mock() -> Session:
    return MagicMock(spec=Session)


def _paginated_query_chain(rows, total, *, with_filter=True, plan_counts=None):
    if plan_counts is None:
        plan_counts = [0] * len(rows)
    query_rows = list(zip(rows, plan_counts))
    query_mock = MagicMock()
    options_mock = MagicMock()
    target = options_mock.filter.return_value if with_filter else options_mock
    target.count.return_value = total
    ordered = MagicMock()
    ordered.offset.return_value.limit.return_value.all.return_value = query_rows
    target.order_by.return_value = ordered
    query_mock.options.return_value = options_mock
    return query_mock


def _random_featured_query_chain(rows, total, *, with_filter=True, plan_counts=None):
    if plan_counts is None:
        plan_counts = [0] * len(rows)
    query_rows = list(zip(rows, plan_counts))
    query_mock = MagicMock()
    options_mock = MagicMock()
    target = options_mock.filter.return_value if with_filter else options_mock
    target.count.return_value = total
    ordered = MagicMock()
    ordered.limit.return_value.all.return_value = query_rows
    target.order_by.return_value = ordered
    query_mock.options.return_value = options_mock
    return query_mock


def test_save_series_success_commits_and_returns_series():
    db = _make_session_mock()
    series = MagicMock(name="SeriesInstance")

    result = save_series_with_plans(db=db, series=series, metadata_entries=[], plans_to_attach=None)

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
        save_series_with_plans(db=db, series=series, metadata_entries=[], plans_to_attach=None)


def test_get_series_paginated_no_search_returns_rows_and_total():
    db = _make_session_mock()
    row1 = MagicMock(spec=Series)
    row2 = MagicMock(spec=Series)

    db.query.return_value = _paginated_query_chain([row1, row2], 2)

    rows, total = get_series_paginated(db=db, search=None, skip=0, limit=10)

    assert total == 2
    assert rows == [(row1, 0, 0), (row2, 0, 0)]
    assert db.query.call_count == 2
    assert db.query.call_args_list[0].args[0] is Series
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
    assert rows == [(row, 0, 0)]
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
    assert rows == [(row, 0, 0)]
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


def test_get_series_paginated_with_author_id_applies_filter():
    db = _make_session_mock()
    row = MagicMock(spec=Series)
    author_id = uuid.uuid4()

    db.query.return_value = _paginated_query_chain([row], 1)

    rows, total = get_series_paginated(
        db=db, search=None, skip=0, limit=10, author_id=author_id
    )

    assert rows == [(row, 0, 0)]
    assert total == 1
    filtered = db.query.return_value.options.return_value.filter
    assert filtered.call_count == 1
    filter_args = filtered.call_args[0]
    assert len(filter_args) == 2


def test_get_series_paginated_with_language_applies_metadata_filter():
    db = _make_session_mock()

    db.query.return_value = _paginated_query_chain([], 0)

    rows, total = get_series_paginated(db=db, search=None, skip=0, limit=10, language="bo")

    assert rows == []
    assert total == 0
    filtered = db.query.return_value.options.return_value.filter
    assert filtered.call_count == 1
    filter_args = filtered.call_args[0]
    assert len(filter_args) == 2


def test_get_series_paginated_returns_series_with_plan_count():
    db = _make_session_mock()
    row = MagicMock(spec=Series)

    db.query.return_value = _paginated_query_chain([row], 1, plan_counts=[5])

    rows, total = get_series_paginated(db=db, search=None, skip=0, limit=10)

    assert total == 1
    assert rows == [(row, 5, 0)]


def test_get_series_paginated_with_status_and_featured_applies_filters():
    db = _make_session_mock()

    db.query.return_value = _paginated_query_chain([], 0)

    rows, total = get_series_paginated(
        db=db,
        search=None,
        skip=0,
        limit=10,
        status=PlanStatus.PUBLISHED,
        featured=True,
    )

    assert rows == []
    assert total == 0
    filtered = db.query.return_value.options.return_value.filter
    assert filtered.call_count == 1
    filter_args = filtered.call_args[0]
    assert len(filter_args) == 3


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


# ---------------------------------------------------------------------------
# display_order persistence: save_series_with_plans (POST path)
# ---------------------------------------------------------------------------

def _capture_plan_updates(db):
    """Collect the dict passed to every Plan .update() call on the mock session.

    Each .update() is reached via db.query(Plan).filter(...).update({...}).
    Returns the list of update-value dicts in call order.
    """
    return [
        call.args[0]
        for call in db.query.return_value.filter.return_value.update.call_args_list
    ]


def test_save_series_with_plans_writes_series_id_and_display_order_per_plan():
    db = _make_session_mock()
    series = MagicMock(name="SeriesInstance")
    series.id = uuid.uuid4()

    plan_a = uuid.uuid4()
    plan_b = uuid.uuid4()
    plan_c = uuid.uuid4()
    plans_to_attach = [(plan_a, 0), (plan_b, 1), (plan_c, 2)]

    save_series_with_plans(
        db=db,
        series=series,
        metadata_entries=[],
        plans_to_attach=plans_to_attach,
    )

    updates = _capture_plan_updates(db)
    # One update issued per plan.
    assert len(updates) == 3
    # Every update sets both series_id and display_order.
    display_orders = [u[Plan.display_order] for u in updates]
    assert display_orders == [0, 1, 2]
    for u in updates:
        assert u[Plan.series_id] == series.id
    db.commit.assert_called_once()


def test_save_series_with_plans_no_plans_issues_no_plan_updates():
    db = _make_session_mock()
    series = MagicMock(name="SeriesInstance")
    series.id = uuid.uuid4()

    save_series_with_plans(
        db=db,
        series=series,
        metadata_entries=[],
        plans_to_attach=None,
    )

    assert _capture_plan_updates(db) == []
    db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# display_order persistence: update_series_with_plans (PUT path)
# ---------------------------------------------------------------------------

def test_update_series_with_plans_attaches_with_display_order():
    db = _make_session_mock()
    series = MagicMock(name="SeriesInstance")
    series.id = uuid.uuid4()

    plan_a = uuid.uuid4()
    plan_b = uuid.uuid4()
    plans_to_attach = [(plan_a, 0), (plan_b, 1)]

    update_series_with_plans(
        db=db,
        series=series,
        image=None,
        featured=False,
        updated_by="tester@example.com",
        plans_to_attach=plans_to_attach,
        plan_ids_to_detach=[],
        updated_at=None,
    )

    updates = _capture_plan_updates(db)
    assert len(updates) == 2
    assert [u[Plan.display_order] for u in updates] == [0, 1]
    for u in updates:
        assert u[Plan.series_id] == series.id
    db.commit.assert_called_once()


def test_update_series_with_plans_detach_resets_series_id_and_display_order():
    db = _make_session_mock()
    series = MagicMock(name="SeriesInstance")
    series.id = uuid.uuid4()

    detach_a = uuid.uuid4()
    detach_b = uuid.uuid4()

    update_series_with_plans(
        db=db,
        series=series,
        image=None,
        featured=False,
        updated_by="tester@example.com",
        plans_to_attach=[],
        plan_ids_to_detach=[detach_a, detach_b],
        updated_at=None,
    )

    updates = _capture_plan_updates(db)
    assert len(updates) == 1
    detach_values = updates[0]
    assert detach_values[Plan.series_id] is None
    assert detach_values[Plan.display_order] is None
    db.commit.assert_called_once()


def test_update_series_with_plans_attach_and_detach_together():
    db = _make_session_mock()
    series = MagicMock(name="SeriesInstance")
    series.id = uuid.uuid4()

    keep_a = uuid.uuid4()
    new_b = uuid.uuid4()
    detach_c = uuid.uuid4()

    update_series_with_plans(
        db=db,
        series=series,
        image=None,
        featured=False,
        updated_by="tester@example.com",
        plans_to_attach=[(keep_a, 0), (new_b, 1)],
        plan_ids_to_detach=[detach_c],
        updated_at=None,
    )

    updates = _capture_plan_updates(db)
    assert len(updates) == 3
    detach_updates = [u for u in updates if u.get(Plan.series_id) is None]
    assert len(detach_updates) == 1
    assert detach_updates[0][Plan.display_order] is None


# ---------------------------------------------------------------------------
# soft delete: soft_delete_series_with_plan_detach (DELETE path)
# ---------------------------------------------------------------------------

def test_soft_delete_series_sets_deleted_fields_and_commits():
    db = _make_session_mock()
    series = MagicMock(name="SeriesInstance")
    series.id = uuid.uuid4()

    soft_delete_series_with_plan_detach(
        db=db,
        series=series,
        deleted_by="tester@example.com",
    )

    assert series.deleted_at is not None
    assert series.deleted_by == "tester@example.com"
    db.commit.assert_called_once()


def test_soft_delete_series_detaches_all_attached_plans():
    db = _make_session_mock()
    series = MagicMock(name="SeriesInstance")
    series.id = uuid.uuid4()

    soft_delete_series_with_plan_detach(
        db=db,
        series=series,
        deleted_by="tester@example.com",
    )

    updates = _capture_plan_updates(db)
    assert len(updates) == 1
    detach_values = updates[0]
    assert detach_values[Plan.series_id] is None
    assert detach_values[Plan.display_order] is None


def test_soft_delete_series_returns_none():
    db = _make_session_mock()
    series = MagicMock(name="SeriesInstance")
    series.id = uuid.uuid4()

    result = soft_delete_series_with_plan_detach(
        db=db,
        series=series,
        deleted_by="tester@example.com",
    )

    assert result is None

# ---------------------------------------------------------------------------
# status update: update_series_status (PATCH /status path)
# ---------------------------------------------------------------------------

def test_update_series_status_sets_status_updated_fields_and_commits():
    db = _make_session_mock()
    series = MagicMock(name="SeriesInstance")
    series.id = uuid.uuid4()
    updated_at = MagicMock(name="UpdatedAt")

    result = update_series_status(
        db=db,
        series=series,
        status="PUBLISHED",
        updated_by="tester@example.com",
        updated_at=updated_at,
    )

    assert result is series
    assert series.status == "PUBLISHED"
    assert series.updated_at is updated_at
    assert series.updated_by == "tester@example.com"
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(series)


def test_update_series_status_integrity_error_propagates():
    db = _make_session_mock()
    series = MagicMock(name="SeriesInstance")
    series.id = uuid.uuid4()
    orig = Exception("constraint violation")
    db.commit.side_effect = IntegrityError("statement", {}, orig)

    with pytest.raises(IntegrityError):
        update_series_status(
            db=db,
            series=series,
            status="PUBLISHED",
            updated_by="tester@example.com",
            updated_at=MagicMock(),
        )


# ---------------------------------------------------------------------------
# featured update: update_series_featured (PATCH /featured path)
# ---------------------------------------------------------------------------

def test_update_series_featured_sets_featured_updated_fields_and_commits():
    db = _make_session_mock()
    series = MagicMock(name="SeriesInstance")
    series.id = uuid.uuid4()
    updated_at = MagicMock(name="UpdatedAt")

    result = update_series_featured(
        db=db,
        series=series,
        featured=True,
        updated_by="tester@example.com",
        updated_at=updated_at,
    )

    assert result is series
    assert series.featured is True
    assert series.updated_at is updated_at
    assert series.updated_by == "tester@example.com"
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(series)


def test_update_series_featured_writes_false_value():
    db = _make_session_mock()
    series = MagicMock(name="SeriesInstance")
    series.id = uuid.uuid4()

    update_series_featured(
        db=db,
        series=series,
        featured=False,
        updated_by="tester@example.com",
        updated_at=MagicMock(),
    )

    assert series.featured is False
    db.commit.assert_called_once()


def test_update_series_featured_integrity_error_propagates():
    db = _make_session_mock()
    series = MagicMock(name="SeriesInstance")
    series.id = uuid.uuid4()
    orig = Exception("constraint violation")
    db.commit.side_effect = IntegrityError("statement", {}, orig)

    with pytest.raises(IntegrityError):
        update_series_featured(
            db=db,
            series=series,
            featured=True,
            updated_by="tester@example.com",
            updated_at=MagicMock(),
        )


# ---------------------------------------------------------------------------
# plan_count published_only filter: get_series_paginated
# ---------------------------------------------------------------------------

def test_get_series_paginated_defaults_published_only_false():
    db = _make_session_mock()
    row = MagicMock(spec=Series)

    db.query.return_value = _paginated_query_chain([row], 1, plan_counts=[7])

    rows, total = get_series_paginated(db=db, search=None, skip=0, limit=10)

    assert total == 1
    assert rows == [(row, 7, 0)]


def test_get_series_paginated_accepts_published_only_true():
    db = _make_session_mock()
    row = MagicMock(spec=Series)

    db.query.return_value = _paginated_query_chain([row], 1, plan_counts=[3])

    rows, total = get_series_paginated(
        db=db, search=None, skip=0, limit=10, published_only=True
    )

    assert total == 1
    assert rows == [(row, 3, 0)]


def test_get_series_paginated_published_only_does_not_add_series_filter():
    db = _make_session_mock()

    db.query.return_value = _paginated_query_chain([], 0)

    rows, total = get_series_paginated(
        db=db,
        search=None,
        skip=0,
        limit=10,
        status=PlanStatus.PUBLISHED,
        featured=True,
        published_only=True,
    )

    assert rows == []
    assert total == 0


def test_get_random_featured_published_series_with_language_applies_metadata_filter():
    db = _make_session_mock()

    db.query.return_value = _random_featured_query_chain([], 0)

    rows, total = get_random_featured_published_series(db=db, limit=10, language="bo")

    assert rows == []
    assert total == 0
    filtered = db.query.return_value.options.return_value.filter
    assert filtered.call_count == 1
    filter_args = filtered.call_args[0]
    assert len(filter_args) == 4


def test_get_random_featured_published_series_without_language_uses_base_filters():
    db = _make_session_mock()
    row = MagicMock(spec=Series)

    db.query.return_value = _random_featured_query_chain([row], 1)

    rows, total = get_random_featured_published_series(db=db, limit=10)

    assert total == 1
    assert rows == [(row, 0, 0)]
    filtered = db.query.return_value.options.return_value.filter
    assert filtered.call_count == 1
    filter_args = filtered.call_args[0]
    assert len(filter_args) == 3
    filtered = db.query.return_value.options.return_value.filter
    assert filtered.call_count == 1
    filter_args = filtered.call_args[0]
    assert len(filter_args) == 3