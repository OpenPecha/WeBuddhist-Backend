from unittest.mock import MagicMock, patch
from uuid import uuid4

from pecha_api.plans.users.plan_users_progress_repository import (
    get_user_series_days_completed_paginated,
    get_user_total_practice_days,
)


def test_get_user_total_practice_days_returns_count():
    user_id = uuid4()
    db = MagicMock()
    db.query.return_value.join.return_value.join.return_value.filter.return_value.scalar.return_value = 15

    assert get_user_total_practice_days(db=db, user_id=user_id) == 15


def test_get_user_total_practice_days_returns_zero_when_no_completions():
    user_id = uuid4()
    db = MagicMock()
    db.query.return_value.join.return_value.join.return_value.filter.return_value.scalar.return_value = None

    assert get_user_total_practice_days(db=db, user_id=user_id) == 0


@patch("pecha_api.plans.users.plan_users_progress_repository.desc", side_effect=lambda column: column)
def test_get_user_series_days_completed_paginated_returns_rows_and_total(_mock_desc):
    user_id = uuid4()
    series_id = uuid4()
    grouped_subq = MagicMock()

    build_query = MagicMock()
    build_query.join.return_value = build_query
    build_query.filter.return_value = build_query
    build_query.group_by.return_value.subquery.return_value = grouped_subq

    total_query = MagicMock()
    total_query.select_from.return_value.scalar.return_value = 2

    rows_query = MagicMock()
    rows_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
        (series_id, 10),
    ]

    db = MagicMock()
    db.query.side_effect = [build_query, total_query, rows_query]

    rows, total = get_user_series_days_completed_paginated(
        db=db,
        user_id=user_id,
        skip=0,
        limit=20,
    )

    assert total == 2
    assert rows == [(series_id, 10)]
    rows_query.order_by.return_value.offset.assert_called_once_with(0)
    rows_query.order_by.return_value.offset.return_value.limit.assert_called_once_with(20)


@patch("pecha_api.plans.users.plan_users_progress_repository.desc", side_effect=lambda column: column)
def test_get_user_series_days_completed_paginated_returns_zero_total_when_empty(_mock_desc):
    user_id = uuid4()
    grouped_subq = MagicMock()

    build_query = MagicMock()
    build_query.join.return_value = build_query
    build_query.filter.return_value = build_query
    build_query.group_by.return_value.subquery.return_value = grouped_subq

    total_query = MagicMock()
    total_query.select_from.return_value.scalar.return_value = None

    rows_query = MagicMock()
    rows_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

    db = MagicMock()
    db.query.side_effect = [build_query, total_query, rows_query]

    rows, total = get_user_series_days_completed_paginated(
        db=db,
        user_id=user_id,
        skip=5,
        limit=10,
    )

    assert total == 0
    assert rows == []
