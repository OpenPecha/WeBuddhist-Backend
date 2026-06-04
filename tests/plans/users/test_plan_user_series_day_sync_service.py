import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from pecha_api.plans.users.plan_user_series_day_sync_service import sync_series_day_completion


def test_sync_series_day_completion_returns_empty_when_day_not_found():
    db_mock = MagicMock()
    with patch(
        "pecha_api.plans.users.plan_user_series_day_sync_service.get_plan_item_by_id",
        return_value=None,
    ):
        result = sync_series_day_completion(db_mock, uuid.uuid4(), uuid.uuid4())
    assert result == []


def test_sync_series_day_completion_returns_empty_when_plan_not_in_series():
    db_mock = MagicMock()
    day_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    with patch(
        "pecha_api.plans.users.plan_user_series_day_sync_service.get_plan_item_by_id",
        return_value=SimpleNamespace(id=day_id, plan_id=plan_id, day_number=1),
    ), patch(
        "pecha_api.plans.users.plan_user_series_day_sync_service.get_plan_by_id",
        return_value=SimpleNamespace(id=plan_id, series_id=None, display_order=1),
    ):
        result = sync_series_day_completion(db_mock, uuid.uuid4(), day_id)
    assert result == []


def test_sync_series_day_completion_returns_empty_when_display_order_missing():
    db_mock = MagicMock()
    day_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    series_id = uuid.uuid4()
    with patch(
        "pecha_api.plans.users.plan_user_series_day_sync_service.get_plan_item_by_id",
        return_value=SimpleNamespace(id=day_id, plan_id=plan_id, day_number=2),
    ), patch(
        "pecha_api.plans.users.plan_user_series_day_sync_service.get_plan_by_id",
        return_value=SimpleNamespace(id=plan_id, series_id=series_id, display_order=None),
    ):
        result = sync_series_day_completion(db_mock, uuid.uuid4(), day_id)
    assert result == []


def test_sync_series_day_completion_marks_sibling_days_complete():
    db_mock = MagicMock()
    user_id = uuid.uuid4()
    completed_day_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    series_id = uuid.uuid4()
    sibling_plan_id = uuid.uuid4()
    sibling_day_id = uuid.uuid4()

    sibling_plan = SimpleNamespace(id=sibling_plan_id)
    sibling_day = SimpleNamespace(id=sibling_day_id)

    with patch(
        "pecha_api.plans.users.plan_user_series_day_sync_service.get_plan_item_by_id",
        return_value=SimpleNamespace(id=completed_day_id, plan_id=plan_id, day_number=3),
    ), patch(
        "pecha_api.plans.users.plan_user_series_day_sync_service.get_plan_by_id",
        return_value=SimpleNamespace(id=plan_id, series_id=series_id, display_order=1),
    ), patch(
        "pecha_api.plans.users.plan_user_series_day_sync_service.get_sibling_plans_in_series_slot",
        return_value=[sibling_plan],
    ) as mock_siblings, patch(
        "pecha_api.plans.users.plan_user_series_day_sync_service.get_plan_items_by_plan_ids_and_day_number",
        return_value=[sibling_day],
    ) as mock_equivalent_days, patch(
        "pecha_api.plans.users.plan_user_series_day_sync_service.save_user_day_completion_if_not_exists",
    ) as mock_save:
        result = sync_series_day_completion(db_mock, user_id, completed_day_id)

    mock_siblings.assert_called_once_with(
        db_mock,
        series_id=series_id,
        display_order=1,
        exclude_plan_id=plan_id,
    )
    mock_equivalent_days.assert_called_once_with(
        db_mock,
        plan_ids=[sibling_plan_id],
        day_number=3,
    )
    mock_save.assert_called_once_with(db_mock, user_id, sibling_day_id)
    assert result == [sibling_day_id]


def test_check_day_completion_runs_plan_completion_for_sibling_days():
    from pecha_api.plans.users.plan_users_service import check_day_completion

    user_id = uuid.uuid4()
    day_id = uuid.uuid4()
    sibling_day_id = uuid.uuid4()
    db_mock = MagicMock()

    with patch(
        "pecha_api.plans.users.plan_users_service.get_tasks_by_plan_item_id",
        return_value=[SimpleNamespace(id=uuid.uuid4())],
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_uncompleted_user_task_ids",
        return_value=[],
    ), patch(
        "pecha_api.plans.users.plan_users_service.save_user_day_completion",
    ), patch(
        "pecha_api.plans.users.plan_users_service.sync_series_day_completion",
        return_value=[sibling_day_id],
    ), patch(
        "pecha_api.plans.users.plan_users_service.check_plan_completion",
    ) as mock_plan_completion:
        check_day_completion(db=db_mock, user_id=user_id, day_id=day_id)

    assert mock_plan_completion.call_count == 2
    mock_plan_completion.assert_any_call(db_mock, user_id, day_id)
    mock_plan_completion.assert_any_call(db_mock, user_id, sibling_day_id)
