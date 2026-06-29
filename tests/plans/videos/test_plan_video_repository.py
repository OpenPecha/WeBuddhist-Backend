from unittest.mock import MagicMock
from uuid import uuid4

from pecha_api.plans.videos.plan_video_repository import get_plan_id_by_segment_id


def _chain_query_returning(scalar_value):
    """Build a MagicMock db whose query(...).join().join().filter()... .scalar()
    returns the given value. Every chained call returns the same mock so the
    builder methods can be invoked in any order."""
    query = MagicMock()
    # all chainable methods return the query mock itself
    for method in ("join", "filter", "order_by", "limit"):
        getattr(query, method).return_value = query
    query.scalar.return_value = scalar_value

    db = MagicMock()
    db.query.return_value = query
    return db, query


def test_get_plan_id_by_segment_id_returns_plan_id():
    plan_id = uuid4()
    db, query = _chain_query_returning(plan_id)

    result = get_plan_id_by_segment_id(db=db, segment_id=uuid4())

    assert result == plan_id
    db.query.assert_called_once()
    # two joins (tasks, sub_tasks), and the result is limited to one row
    assert query.join.call_count == 2
    query.limit.assert_called_once_with(1)
    query.scalar.assert_called_once()


def test_get_plan_id_by_segment_id_returns_none_when_no_match():
    db, query = _chain_query_returning(None)

    result = get_plan_id_by_segment_id(db=db, segment_id=uuid4())

    assert result is None
    query.scalar.assert_called_once()
