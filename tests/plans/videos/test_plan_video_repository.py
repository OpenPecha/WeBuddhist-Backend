from unittest.mock import MagicMock
from uuid import uuid4

from pecha_api.plans.videos.plan_video_repository import (
    get_plan_videos_by_segment_id,
    get_sibling_language_plan_ids,
)


def _chain_query_returning(rows):
    """Build a MagicMock db whose query(...).join()...filter()...order_by().all()
    returns the given rows. Every chained builder returns the same mock."""
    query = MagicMock()
    for method in ("join", "filter", "order_by"):
        getattr(query, method).return_value = query
    query.all.return_value = rows

    db = MagicMock()
    db.query.return_value = query
    return db, query


def test_get_plan_videos_by_segment_id_returns_rows():
    rows = [MagicMock(), MagicMock()]
    db, query = _chain_query_returning(rows)

    result = get_plan_videos_by_segment_id(db=db, segment_id=uuid4())

    assert result == rows
    db.query.assert_called_once()
    # three joins: plan_videos -> items -> tasks -> sub_tasks
    assert query.join.call_count == 3
    query.all.assert_called_once()


def test_get_plan_videos_by_segment_id_returns_empty_when_no_match():
    db, query = _chain_query_returning([])

    result = get_plan_videos_by_segment_id(db=db, segment_id=uuid4())

    assert result == []
    query.all.assert_called_once()


def _sibling_db(plan, sibling_rows):
    """db where query(Plan).filter().first() -> plan and the sibling-id
    query().filter().all() -> sibling_rows (list of 1-tuples)."""
    plan_query = MagicMock()
    plan_query.filter.return_value = plan_query
    plan_query.first.return_value = plan

    sibling_query = MagicMock()
    sibling_query.filter.return_value = sibling_query
    sibling_query.all.return_value = sibling_rows

    db = MagicMock()
    # first db.query(...) -> plan lookup, second -> sibling lookup
    db.query.side_effect = [plan_query, sibling_query]
    return db, sibling_query


def _plan(*, series_id, display_order):
    p = MagicMock()
    p.id = uuid4()
    p.series_id = series_id
    p.display_order = display_order
    return p


def test_sibling_ids_standalone_plan_returns_only_self():
    plan = _plan(series_id=None, display_order=0)
    db, _ = _sibling_db(plan, [])

    result = get_sibling_language_plan_ids(db=db, plan_id=plan.id)

    assert result == [plan.id]
    # no second (sibling) query was issued
    assert db.query.call_count == 1


def test_sibling_ids_null_display_order_returns_only_self():
    # Regression: a NULL display_order must NOT fan out to every unordered
    # plan in the series (== None compiles to IS NULL).
    plan = _plan(series_id=uuid4(), display_order=None)
    db, _ = _sibling_db(plan, [])

    result = get_sibling_language_plan_ids(db=db, plan_id=plan.id)

    assert result == [plan.id]
    assert db.query.call_count == 1  # sibling query skipped


def test_sibling_ids_returns_all_language_siblings():
    plan = _plan(series_id=uuid4(), display_order=0)
    bo_id, zh_id = uuid4(), uuid4()
    # sibling query returns rows (1-tuples), including the plan itself
    db, _ = _sibling_db(plan, [(plan.id,), (bo_id,), (zh_id,)])

    result = get_sibling_language_plan_ids(db=db, plan_id=plan.id)

    assert set(result) == {plan.id, bo_id, zh_id}
    assert db.query.call_count == 2


def test_sibling_ids_appends_self_when_missing_from_query():
    plan = _plan(series_id=uuid4(), display_order=0)
    bo_id = uuid4()
    # sibling query somehow omits the plan itself -> it must still be included
    db, _ = _sibling_db(plan, [(bo_id,)])

    result = get_sibling_language_plan_ids(db=db, plan_id=plan.id)

    assert plan.id in result
    assert set(result) == {plan.id, bo_id}
