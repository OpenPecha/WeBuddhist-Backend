import uuid
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from pecha_api.plans.groups.groups_repository import (
    get_group_id_for_plan,
    get_group_id_for_series,
    get_group_ids_by_plan_ids,
    get_group_ids_by_series_ids,
    update_group,
)


def _make_session_mock() -> Session:
    return MagicMock(spec=Session)


def test_get_group_ids_by_plan_ids_returns_first_group_per_plan():
    db = _make_session_mock()
    plan_id = uuid.uuid4()
    group_id = uuid.uuid4()
    db.execute.return_value.all.return_value = [(plan_id, group_id)]

    result = get_group_ids_by_plan_ids(db=db, plan_ids=[plan_id])

    assert result == {plan_id: group_id}


def test_get_group_id_for_plan():
    db = _make_session_mock()
    plan_id = uuid.uuid4()
    group_id = uuid.uuid4()
    db.execute.return_value.first.return_value = (group_id,)

    assert get_group_id_for_plan(db=db, plan_id=plan_id) == group_id


def test_get_group_ids_by_plan_ids_empty_input():
    db = _make_session_mock()

    assert get_group_ids_by_plan_ids(db=db, plan_ids=[]) == {}
    db.execute.assert_not_called()


def test_get_group_ids_by_series_ids_returns_first_group_per_series():
    db = _make_session_mock()
    series_id = uuid.uuid4()
    group_id = uuid.uuid4()
    db.execute.return_value.all.return_value = [(series_id, group_id)]

    result = get_group_ids_by_series_ids(db=db, series_ids=[series_id])

    assert result == {series_id: group_id}


def test_get_group_id_for_series():
    db = _make_session_mock()
    series_id = uuid.uuid4()
    group_id = uuid.uuid4()
    db.execute.return_value.first.return_value = (group_id,)

    assert get_group_id_for_series(db=db, series_id=series_id) == group_id


def test_get_group_ids_by_series_ids_empty_input():
    db = _make_session_mock()

    assert get_group_ids_by_series_ids(db=db, series_ids=[]) == {}
    db.execute.assert_not_called()


def test_update_group_commits_without_re_adding_instance():
    db = _make_session_mock()
    group = MagicMock()

    result = update_group(db=db, group=group)

    db.add.assert_not_called()
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(group)
    assert result is group
