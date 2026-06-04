from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from pecha_api.plans.items.plan_items_models import PlanItem
from pecha_api.plans.plans_models import Plan


def get_sibling_plans_in_series_slot(
    db: Session,
    *,
    series_id: UUID,
    display_order: int,
    exclude_plan_id: UUID,
) -> List[Plan]:
    """Plans in the same series slot (display_order) as the source plan, excluding the source."""
    return (
        db.query(Plan)
        .filter(
            Plan.series_id == series_id,
            Plan.display_order == display_order,
            Plan.id != exclude_plan_id,
            Plan.deleted_at.is_(None),
        )
        .all()
    )


def get_plan_items_by_plan_ids_and_day_number(
    db: Session,
    *,
    plan_ids: List[UUID],
    day_number: int,
) -> List[PlanItem]:
    if not plan_ids:
        return []
    return (
        db.query(PlanItem)
        .filter(
            and_(
                PlanItem.plan_id.in_(plan_ids),
                PlanItem.day_number == day_number,
            )
        )
        .all()
    )
