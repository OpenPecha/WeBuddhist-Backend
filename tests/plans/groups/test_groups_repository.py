import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from pecha_api.plans.groups.groups_repository import (
    clear_user_series_partner_ids_for_group,
    get_group_id_for_plan,
    get_group_id_for_series,
    get_group_ids_by_plan_ids,
    get_group_ids_by_series_ids,
    get_groups_paginated,
    get_series_by_group_id,
    get_series_partner_id_map_for_group,
    get_user_series_enrollment_partner_map,
    leave_group_membership,
    update_group,
)
from pecha_api.plans.users.plan_users_models import UserSeriesEnrollment


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


def test_get_series_partner_id_map_for_group_empty_input():
    db = _make_session_mock()
    assert get_series_partner_id_map_for_group(db=db, group_id=uuid.uuid4(), series_ids=[]) == {}


def test_get_series_partner_id_map_for_group():
    db = _make_session_mock()
    group_id = uuid.uuid4()
    series_id = uuid.uuid4()
    partner_id = uuid.uuid4()
    db.execute.return_value.all.return_value = [(series_id, partner_id)]

    result = get_series_partner_id_map_for_group(
        db=db, group_id=group_id, series_ids=[series_id]
    )

    assert result == {series_id: partner_id}


def test_get_user_series_enrollment_partner_map_empty_input():
    db = _make_session_mock()
    assert get_user_series_enrollment_partner_map(
        db=db, user_id=uuid.uuid4(), series_ids=[]
    ) == {}


def test_get_user_series_enrollment_partner_map():
    db = _make_session_mock()
    user_id = uuid.uuid4()
    series_id = uuid.uuid4()
    partner_id = uuid.uuid4()
    db.execute.return_value.all.return_value = [(series_id, partner_id)]

    result = get_user_series_enrollment_partner_map(
        db=db, user_id=user_id, series_ids=[series_id]
    )

    assert result == {series_id: partner_id}


def test_get_series_by_group_id_includes_owned_and_partner_series():
    db = _make_session_mock()
    group_id = uuid.uuid4()
    owned_series = MagicMock()
    partner_series = MagicMock()
    query = MagicMock()
    db.query.return_value = query
    query.outerjoin.return_value = query
    query.filter.return_value = query
    query.distinct.return_value = query
    query.distinct.return_value.all.return_value = [owned_series, partner_series]

    result = get_series_by_group_id(db=db, group_id=group_id)

    assert result == [owned_series, partner_series]
    db.query.assert_called_once()
    query.outerjoin.assert_called_once()
    query.filter.assert_called_once()
    query.distinct.assert_called_once()


def test_update_group_commits_without_re_adding_instance():
    db = _make_session_mock()
    group = MagicMock()

    result = update_group(db=db, group=group)

    db.add.assert_not_called()
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(group)
    assert result is group


def test_get_groups_paginated_with_exclude_group_ids():
    db = _make_session_mock()
    query = MagicMock()
    db.query.return_value = query
    query.options.return_value = query
    query.filter.return_value = query
    query.count.return_value = 0
    query.order_by.return_value = query
    query.offset.return_value = query
    query.limit.return_value.all.return_value = []

    groups, total = get_groups_paginated(
        db=db,
        skip=0,
        limit=10,
        exclude_group_ids=[uuid.uuid4()],
    )

    assert groups == []
    assert total == 0
    query.filter.assert_called_once()


def test_clear_user_series_partner_ids_for_group_returns_zero_when_no_partners():
    db = _make_session_mock()
    db.execute.return_value.all.return_value = []

    result = clear_user_series_partner_ids_for_group(
        db=db, user_id=uuid.uuid4(), group_id=uuid.uuid4()
    )

    assert result == 0
    db.query.assert_not_called()
    db.commit.assert_called_once()


def test_clear_user_series_partner_ids_for_group_clears_matching_enrollments():
    db = _make_session_mock()
    user_id = uuid.uuid4()
    group_id = uuid.uuid4()
    partner_id = uuid.uuid4()
    db.execute.return_value.all.return_value = [(partner_id,)]
    query = MagicMock()
    db.query.return_value = query
    query.filter.return_value = query
    query.update.return_value = 2

    result = clear_user_series_partner_ids_for_group(
        db=db, user_id=user_id, group_id=group_id
    )

    assert result == 2
    query.update.assert_called_once()
    update_values = query.update.call_args.args[0]
    assert update_values[UserSeriesEnrollment.series_partner_id] is None
    db.commit.assert_called_once()


def test_leave_group_membership_commits_once_after_join_removal_and_partner_cleanup():
    db = _make_session_mock()
    user_id = uuid.uuid4()
    group_id = uuid.uuid4()
    partner_id = uuid.uuid4()
    db.execute.return_value.all.return_value = [(partner_id,)]
    query = MagicMock()
    db.query.return_value = query
    query.filter.return_value = query
    query.update.return_value = 1

    leave_group_membership(db=db, user_id=user_id, group_id=group_id)

    assert db.execute.call_count == 2
    query.update.assert_called_once()
    db.commit.assert_called_once()


def test_leave_group_membership_commits_once_when_group_has_no_partner_series():
    db = _make_session_mock()
    user_id = uuid.uuid4()
    group_id = uuid.uuid4()
    db.execute.return_value.all.return_value = []

    leave_group_membership(db=db, user_id=user_id, group_id=group_id)

    assert db.execute.call_count == 2
    db.query.assert_not_called()
    db.commit.assert_called_once()


def test_leave_group_membership_does_not_commit_when_partner_cleanup_fails():
    db = _make_session_mock()
    user_id = uuid.uuid4()
    group_id = uuid.uuid4()
    partner_id = uuid.uuid4()
    db.execute.return_value.all.return_value = [(partner_id,)]
    query = MagicMock()
    db.query.return_value = query
    query.filter.return_value = query
    query.update.side_effect = RuntimeError("db error")

    with pytest.raises(RuntimeError, match="db error"):
        leave_group_membership(db=db, user_id=user_id, group_id=group_id)

    db.commit.assert_not_called()
