from unittest.mock import MagicMock
from uuid import uuid4

from pecha_api.group_accumulator.group_accumulator_repository import (
    get_joined_group_accumulator_ids_by_user,
    is_user_joined_group_accumulator,
)


def test_is_user_joined_group_accumulator_checks_join_table():
    db = MagicMock()
    group_accumulator_id = uuid4()
    user_id = uuid4()
    db.execute.return_value.first.return_value = (group_accumulator_id,)

    assert is_user_joined_group_accumulator(
        db=db,
        group_accumulator_id=group_accumulator_id,
        user_id=user_id,
    )


def test_is_user_joined_group_accumulator_false_when_no_join_row():
    db = MagicMock()
    db.execute.return_value.first.return_value = None

    assert not is_user_joined_group_accumulator(
        db=db,
        group_accumulator_id=uuid4(),
        user_id=uuid4(),
    )


def test_get_joined_group_accumulator_ids_by_user_reads_join_table():
    db = MagicMock()
    joined_id = uuid4()
    query = MagicMock()
    db.query.return_value = query
    query.filter.return_value = query
    query.all.return_value = [MagicMock(group_accumulator_id=joined_id)]

    result = get_joined_group_accumulator_ids_by_user(
        db=db,
        user_id=uuid4(),
        group_accumulator_ids=[joined_id],
    )

    assert result == [joined_id]
    db.query.assert_called_once()
