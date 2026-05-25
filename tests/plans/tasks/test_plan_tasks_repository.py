import uuid
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import IntegrityError

from pecha_api.plans.response_message import BAD_REQUEST, TASK_NOT_FOUND
# Ensure sub-task relationship backref is registered on PlanTask before repository import
from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_models import PlanSubTask  # noqa: F401
from pecha_api.plans.tasks.plan_tasks_repository import (
    save_task,
    get_tasks_by_item_ids,
    get_task_by_id,
    update_task_day,
    update_task_title,
    get_tasks_by_plan_item_id,
    reorder_day_tasks_display_order,
)


def test_save_task_success_sets_id_and_returns_object():
    db = MagicMock()

    def _refresh_side_effect(obj):
        if not getattr(obj, "id", None):
            obj.id = uuid.uuid4()

    db.refresh.side_effect = _refresh_side_effect

    new_task = SimpleNamespace()
    result = save_task(db=db, new_task=new_task)

    assert result is new_task
    assert getattr(result, "id", None) is not None
    assert db.add.call_count == 1
    assert db.commit.call_count == 1
    assert db.refresh.call_count == 1


def test_save_task_integrity_error_rolls_back_and_raises_http_exception():
    db = MagicMock()
    db.add.return_value = None
    db.commit.side_effect = IntegrityError(statement=None, params=None, orig=Exception("fail"))

    with pytest.raises(Exception) as exc:
        save_task(db=db, new_task=SimpleNamespace())

    assert db.rollback.call_count == 1
    from fastapi import HTTPException  # local import for assertion

    assert isinstance(exc.value, HTTPException)
    assert exc.value.status_code == 400
    assert exc.value.detail["error"] == BAD_REQUEST
    assert "fail" in exc.value.detail["message"]


def test_get_tasks_by_item_ids_empty_returns_empty_mapping():
    db = MagicMock()
    result = get_tasks_by_item_ids(db=db, plan_item_ids=[])
    assert result == {}


def test_get_tasks_by_item_ids_queries_and_returns_list():
    db = MagicMock()
    expected = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = expected

    ids = [uuid.uuid4(), uuid.uuid4()]
    result = get_tasks_by_item_ids(db=db, plan_item_ids=ids)

    assert result == expected
    assert db.query.call_count == 1


def test_get_task_by_id_queries_by_id():
    db = MagicMock()
    expected = SimpleNamespace(id=123)
    db.query.return_value.options.return_value.filter.return_value.first.return_value = expected

    task_id = uuid.uuid4()
    from pecha_api.plans.tasks.plan_tasks_repository import PlanTask as _RepoPlanTask
    setattr(_RepoPlanTask, "sub_tasks", object())
    setattr(PlanSubTask, "timestamp", object())
    with patch("pecha_api.plans.tasks.plan_tasks_repository.joinedload") as mock_joined:
        mock_chain = MagicMock()
        mock_joined.return_value = mock_chain
        mock_chain.joinedload.return_value = MagicMock()
        result = get_task_by_id(db=db, task_id=task_id)

    assert result is expected
    assert db.query.call_count == 1


def test_update_task_day_commits_and_refreshes_updated_task():
    db = MagicMock()
    task_id = uuid.uuid4()
    target_day_id = uuid.uuid4()

    updated_task = SimpleNamespace(id=task_id, plan_item_id=target_day_id, display_order=5)

    result = update_task_day(db=db, updated_task=updated_task)

    assert result is updated_task
    assert db.commit.call_count == 1
    assert db.refresh.call_count == 1
    # ensure refresh called on the same object
    assert db.refresh.call_args[0][0] is updated_task


def test_get_task_by_id_not_found_raises_http_404_with_payload():
    db = MagicMock()
    db.query.return_value.options.return_value.filter.return_value.first.return_value = None

    from fastapi import HTTPException

    from pecha_api.plans.tasks.plan_tasks_repository import PlanTask as _RepoPlanTask
    setattr(_RepoPlanTask, "sub_tasks", object())
    setattr(PlanSubTask, "timestamp", object())
    with patch("pecha_api.plans.tasks.plan_tasks_repository.joinedload") as mock_joined:
        mock_chain = MagicMock()
        mock_joined.return_value = mock_chain
        mock_chain.joinedload.return_value = MagicMock()
        with pytest.raises(HTTPException) as exc:
            get_task_by_id(db=db, task_id=uuid.uuid4())

    assert exc.value.status_code == 404
    assert exc.value.detail["error"] == BAD_REQUEST
    assert exc.value.detail["message"] == TASK_NOT_FOUND


def test_delete_task_success_deletes_and_commits():
    db = MagicMock()
    task_id = uuid.uuid4()
    task_obj = SimpleNamespace(id=task_id)

    with patch(
        "pecha_api.plans.tasks.plan_tasks_repository.get_task_by_id",
        return_value=task_obj,
    ) as mock_get:
        # After deletion, repository returns None for the deleted task
        db.query.return_value.filter.return_value.first.return_value = None

        from pecha_api.plans.tasks.plan_tasks_repository import delete_task

        result = delete_task(db=db, task_id=task_id)

        assert mock_get.call_count == 1
        assert db.delete.call_count == 1
        assert db.commit.call_count == 1
        assert result is None


def test_delete_task_error_rolls_back_and_raises_http_exception():
    db = MagicMock()
    task_id = uuid.uuid4()
    task_obj = SimpleNamespace(id=task_id)

    with patch(
        "pecha_api.plans.tasks.plan_tasks_repository.get_task_by_id",
        return_value=task_obj,
    ) as mock_get:
        db.delete.side_effect = Exception("boom")

        from fastapi import HTTPException
        from pecha_api.plans.tasks.plan_tasks_repository import delete_task

        with pytest.raises(HTTPException) as exc:
            delete_task(db=db, task_id=task_id)

        assert exc.value.status_code == 400
        assert exc.value.detail["error"] == BAD_REQUEST


def test_update_task_title_success():
    db = MagicMock()
    task_id = uuid.uuid4()
    new_title = "Updated Task Title"

    updated_task = SimpleNamespace(
        id=task_id,
        title=new_title,
        description="Task description",
        display_order=1,
    )

    result = update_task_title(db=db, updated_task=updated_task)

    assert result is updated_task
    assert result.title == new_title
    assert result.id == task_id

    assert db.commit.call_count == 1
    assert db.refresh.call_count == 1


def test_get_tasks_by_plan_item_id_filters_and_orders():
    db = MagicMock()

    expected = [SimpleNamespace(id=1, display_order=1), SimpleNamespace(id=2, display_order=2)]
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = expected

    plan_item_id = uuid.uuid4()
    result = get_tasks_by_plan_item_id(db=db, plan_item_id=plan_item_id)

    assert result == expected
    assert db.query.call_count == 1
    # ensure filter called with correct criterion object
    assert db.query.return_value.filter.call_count == 1
    assert db.query.return_value.filter.return_value.order_by.call_count == 1


# Removed: update_task_order_by_id no longer exists in repository


def test_reorder_day_tasks_display_order_commits_and_refreshes_each_task():
    db = MagicMock()
    tasks = [SimpleNamespace(id=1), SimpleNamespace(id=2), SimpleNamespace(id=3)]

    reorder_day_tasks_display_order(db=db, tasks=tasks)

    # commit once per task
    assert db.commit.call_count == len(tasks)
    # refresh called for each specific task
    refreshed = [call_args[0][0] for call_args in db.refresh.call_args_list]
    assert refreshed == tasks


def test_reorder_day_tasks_display_order_rolls_back_and_raises_on_error():
    db = MagicMock()
    tasks = [SimpleNamespace(id=1)]
    db.commit.side_effect = Exception("boom")

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        reorder_day_tasks_display_order(db=db, tasks=tasks)

    assert exc.value.status_code == 400
    assert exc.value.detail["error"] == BAD_REQUEST
    assert db.rollback.call_count == 1


# Removed: task-not-found handled at service layer, repository only commits/refreses


def test_update_task_title_empty_string():
    db = MagicMock()
    task_id = uuid.uuid4()

    updated_task = SimpleNamespace(
        id=task_id,
        title="",
        description="Task description",
        display_order=1,
    )

    result = update_task_title(db=db, updated_task=updated_task)

    assert result is updated_task
    assert result.title == ""
    assert result.id == task_id

    assert db.commit.call_count == 1
    assert db.refresh.call_count == 1


def test_update_task_title_database_commit_error():
    db = MagicMock()
    task_id = uuid.uuid4()
    new_title = "Updated Task Title"
    
    updated_task = SimpleNamespace(
        id=task_id,
        title=new_title,
        description="Task description",
        display_order=1,
    )
    
    db.commit.side_effect = Exception("Database connection error")
    
    with pytest.raises(Exception) as exc:
        update_task_title(db=db, updated_task=updated_task)
    
    assert str(exc.value) == "Database connection error"
    assert db.commit.call_count == 1
    assert db.refresh.call_count == 0


def test_update_task_title_preserves_other_fields():
    db = MagicMock()
    task_id = uuid.uuid4()
    new_title = "Updated Task Title"
    
    updated_task = SimpleNamespace(
        id=task_id,
        title=new_title,
        description="Important description",
        display_order=5,
        estimated_time=30,
        created_by="author@example.com",
    )
    
    original_description = updated_task.description
    original_display_order = updated_task.display_order
    original_estimated_time = updated_task.estimated_time
    original_created_by = updated_task.created_by
    
    result = update_task_title(db=db, updated_task=updated_task)
    
    assert result.title == new_title
    assert result.description == original_description
    assert result.display_order == original_display_order
    assert result.estimated_time == original_estimated_time
    assert result.created_by == original_created_by
    
    assert db.commit.call_count == 1
    assert db.refresh.call_count == 1

