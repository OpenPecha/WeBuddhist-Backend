from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from pecha_api.plans.cms.cms_plans_repository import get_plan_by_id
from pecha_api.plans.items.plan_items_repository import get_plan_item_by_id
from pecha_api.plans.users.plan_user_day_repository import save_user_day_completion_if_not_exists
from pecha_api.plans.users.plan_user_series_day_sync_repository import (
    get_plan_items_by_plan_ids_and_day_number,
    get_sibling_plans_in_series_slot,
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
        save_user_day_completion_if_not_exists(db, user_id, equivalent_day.id)
        synced_day_ids.append(equivalent_day.id)

    return synced_day_ids
