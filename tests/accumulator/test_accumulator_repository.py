from unittest.mock import MagicMock, patch
from uuid import uuid4

from pecha_api.accumulator.accumulator_repository import (
    get_accumulator_with_history,
    get_user_total_counted_by_parent,
)


def test_get_user_total_counted_by_parent_sums_history_across_preset_instances():
    db = MagicMock()
    user_id = uuid4()
    parent_id = uuid4()

    query = MagicMock()
    db.query.return_value = query
    query.join.return_value = query
    query.filter.return_value = query
    query.scalar.return_value = 150

    result = get_user_total_counted_by_parent(db, user_id, parent_id)

    assert result == 150
    query.join.assert_called_once()
    query.filter.assert_called_once()
    query.scalar.assert_called_once()


def test_get_user_total_counted_by_parent_returns_zero_when_no_history():
    db = MagicMock()
    query = MagicMock()
    db.query.return_value = query
    query.join.return_value = query
    query.filter.return_value = query
    query.scalar.return_value = None

    result = get_user_total_counted_by_parent(db, uuid4(), uuid4())

    assert result == 0


@patch("pecha_api.accumulator.accumulator_repository.get_user_total_counted_by_parent")
@patch("pecha_api.accumulator.accumulator_repository.get_user_accumulator_by_parent")
def test_get_accumulator_with_history_uses_parent_lifetime_total_not_current_only(
    mock_get_by_parent,
    mock_total_by_parent,
):
    db = MagicMock()
    user_id = uuid4()
    parent_id = uuid4()
    accumulator_id = uuid4()

    accumulator = MagicMock()
    accumulator.id = accumulator_id
    mock_get_by_parent.return_value = accumulator
    mock_total_by_parent.return_value = 300

    history_query = MagicMock()
    db.query.return_value = history_query
    history_query.filter.return_value = history_query
    history_query.order_by.return_value = history_query
    history_query.all.return_value = []

    result = get_accumulator_with_history(db, user_id, parent_id)

    assert result is not None
    returned_accumulator, total_counted, sessions = result
    assert returned_accumulator is accumulator
    assert total_counted == 300
    assert sessions == []
    mock_get_by_parent.assert_called_once_with(db, user_id, parent_id)
    mock_total_by_parent.assert_called_once_with(db, user_id, parent_id)
