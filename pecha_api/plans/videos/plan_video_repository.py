from typing import List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from pecha_api.plans.items.plan_items_models import PlanItem
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.tasks.plan_tasks_models import PlanTask
from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_models import PlanSubTask
from pecha_api.plans.videos.plan_video_models import PlanVideo


def get_sibling_language_plan_ids(db: Session, plan_id: UUID) -> List[UUID]:
    """Return the ids of the plan plus all its language siblings.
    """
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if plan is None:
        return [plan_id]
    if plan.series_id is None:
        return [plan.id]

    siblings = (
        db.query(Plan.id)
        .filter(
            Plan.series_id == plan.series_id,
            Plan.display_order == plan.display_order,
            Plan.deleted_at.is_(None),
        )
        .all()
    )
    plan_ids = [row[0] for row in siblings]
    if plan.id not in plan_ids:
        plan_ids.append(plan.id)
    return plan_ids


def get_plan_videos_by_segment_id(db: Session, segment_id: UUID) -> List[PlanVideo]:
    """Return videos for every plan a segment belongs to, via its sub-task source.

    Chain: sub_tasks.segment_ids -> tasks -> items -> plan_id -> plan_videos.
    A segment may belong to multiple plans; videos from all of them are returned
    in a single query, ordered by plan then display order. De-duplication of
    videos shared across plans is handled by the caller.
    """
    return (
        db.query(PlanVideo)
        .join(PlanItem, PlanItem.plan_id == PlanVideo.plan_id)
        .join(PlanTask, PlanTask.plan_item_id == PlanItem.id)
        .join(PlanSubTask, PlanSubTask.task_id == PlanTask.id)
        .filter(PlanSubTask.segment_ids.any(segment_id))
        .filter(PlanSubTask.deleted_at.is_(None))
        .order_by(
            PlanItem.day_number.asc(),
            PlanTask.display_order.asc(),
            PlanVideo.display_order.asc(),
            PlanVideo.created_at.asc(),
        )
        .all()
    )


def get_plan_videos_by_plan_id(db: Session, plan_id: UUID) -> List[PlanVideo]:
    return (
        db.query(PlanVideo)
        .filter(PlanVideo.plan_id == plan_id)
        .order_by(PlanVideo.display_order.asc(), PlanVideo.created_at.asc())
        .all()
    )


def get_plan_video_by_id(db: Session, plan_id: UUID, video_id: UUID) -> Optional[PlanVideo]:
    return (
        db.query(PlanVideo)
        .filter(PlanVideo.id == video_id, PlanVideo.plan_id == plan_id)
        .first()
    )


def get_next_display_order(db: Session, plan_id: UUID) -> int:
    current_max = (
        db.query(func.max(PlanVideo.display_order))
        .filter(PlanVideo.plan_id == plan_id)
        .scalar()
    )
    return 0 if current_max is None else current_max + 1


def create_plan_video(db: Session, plan_video: PlanVideo) -> PlanVideo:
    db.add(plan_video)
    db.commit()
    db.refresh(plan_video)
    return plan_video


def delete_plan_video(db: Session, plan_id: UUID, video_id: UUID) -> None:
    db.query(PlanVideo).filter(
        PlanVideo.id == video_id, PlanVideo.plan_id == plan_id
    ).delete()
    db.commit()


def delete_plan_video_across_plans(
    db: Session,
    plan_ids: List[UUID],
    video_identity_id: Optional[str],
    url: str,
) -> None:
    """Delete the matching video from every given plan.
    """
    query = db.query(PlanVideo).filter(PlanVideo.plan_id.in_(plan_ids))
    if video_identity_id:
        query = query.filter(PlanVideo.video_id == video_identity_id)
    else:
        query = query.filter(PlanVideo.url == url)
    query.delete(synchronize_session=False)
    db.commit()


def reorder_plan_videos(db: Session, plan_id: UUID, order_by_id: dict) -> None:
    videos = db.query(PlanVideo).filter(PlanVideo.plan_id == plan_id).all()
    for video in videos:
        if video.id in order_by_id:
            video.display_order = order_by_id[video.id]
    db.commit()


def reorder_plan_videos_across_plans(
    db: Session,
    plan_ids: List[UUID],
    order_by_identity: dict,
) -> None:
    """Apply a new display order to every given plan, matched by video identity.

    """
    videos = db.query(PlanVideo).filter(PlanVideo.plan_id.in_(plan_ids)).all()
    for video in videos:
        identity = video.video_id or video.url
        if identity in order_by_identity:
            video.display_order = order_by_identity[identity]
    db.commit()
