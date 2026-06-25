from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from pecha_api.plans.cms.cms_plans_repository import get_plan_by_id
from pecha_api.plans.items.plan_items_repository import get_plan_item_by_id
from pecha_api.plans.tasks.plan_tasks_repository import get_tasks_by_plan_item_id
from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_repository import get_sub_tasks_by_task_id
from pecha_api.plans.users.plan_user_day_repository import save_user_day_completion_if_not_exists
from pecha_api.daily_log.daily_log_cache_service import schedule_invalidate_user_stats_cache
from pecha_api.plans.users.plan_user_series_day_sync_repository import (
    get_plan_items_by_plan_ids_and_day_number,
    get_sibling_plans_in_series_slot,
)
from pecha_api.plans.users.plan_user_task_repository import (
    get_uncompleted_user_task_ids,
    save_user_task_completions_bulk,
)
from pecha_api.plans.users.plan_users_models import UserSubTaskCompletion, UserTaskCompletion
from pecha_api.plans.users.plan_users_subtasks_repository import (
    get_uncompleted_user_sub_task_ids,
    save_user_sub_task_completions_bulk,
)


def _complete_all_tasks_for_day(db: Session, user_id: UUID, day_id: UUID) -> None:
    """Mark every task and subtask in a day as completed for the user."""
    tasks = get_tasks_by_plan_item_id(db, day_id)
    if not tasks:
        return

    task_ids = [task.id for task in tasks]
    uncompleted_task_ids = get_uncompleted_user_task_ids(db, user_id, task_ids)
    if uncompleted_task_ids:
        save_user_task_completions_bulk(
            db,
            [UserTaskCompletion(user_id=user_id, task_id=task_id) for task_id in uncompleted_task_ids],
        )

    sub_task_ids = [
        sub_task.id
        for task in tasks
        for sub_task in get_sub_tasks_by_task_id(db, task.id)
    ]
    if not sub_task_ids:
        return

    uncompleted_sub_task_ids = get_uncompleted_user_sub_task_ids(db, user_id, sub_task_ids)
    if uncompleted_sub_task_ids:
        save_user_sub_task_completions_bulk(
            db,
            [
                UserSubTaskCompletion(user_id=user_id, sub_task_id=sub_task_id)
                for sub_task_id in uncompleted_sub_task_ids
            ],
        )


def sync_series_day_completion(db: Session, user_id: UUID, completed_day_id: UUID) -> List[UUID]:
    """
    Mirror day completion to sibling language plans in the same series slot.

    Sibling plans share series_id and display_order; equivalent days share day_number.
    Returns day_ids of sibling plans that have a matching day (for plan-completion checks).
    """
    day_item = get_plan_item_by_id(db, completed_day_id)
    if not day_item:
        return []

    plan = get_plan_by_id(db, day_item.plan_id)
    if not plan or not plan.series_id or plan.display_order is None:
        return []

    sibling_plans = get_sibling_plans_in_series_slot(
        db,
        series_id=plan.series_id,
        display_order=plan.display_order,
        exclude_plan_id=plan.id,
    )
    if not sibling_plans:
        return []

    equivalent_days = get_plan_items_by_plan_ids_and_day_number(
        db,
        plan_ids=[sibling.id for sibling in sibling_plans],
        day_number=day_item.day_number,
    )

    synced_day_ids: List[UUID] = []
    for equivalent_day in equivalent_days:
        _complete_all_tasks_for_day(db, user_id, equivalent_day.id)
        if save_user_day_completion_if_not_exists(db, user_id, equivalent_day.id):
            schedule_invalidate_user_stats_cache(user_id=user_id)
        synced_day_ids.append(equivalent_day.id)

    return synced_day_ids
