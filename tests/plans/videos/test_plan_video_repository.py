from unittest.mock import MagicMock
from uuid import uuid4

from pecha_api.plans.videos.plan_video_repository import get_plan_videos_by_segment_id


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
