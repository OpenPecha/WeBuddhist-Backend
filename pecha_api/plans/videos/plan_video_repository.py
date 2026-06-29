from typing import List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from pecha_api.plans.items.plan_items_models import PlanItem
from pecha_api.plans.tasks.plan_tasks_models import PlanTask
from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_models import PlanSubTask
from pecha_api.plans.videos.plan_video_models import PlanVideo


def get_plan_id_by_segment_id(db: Session, segment_id: UUID) -> Optional[UUID]:
    """Resolve the plan a segment belongs to via its sub-task source.

    Chain: sub_tasks.segment_ids -> tasks -> items -> plan_id.
    Assumes a segment belongs to a single plan; returns the first match.
    """
    return (
        db.query(PlanItem.plan_id)
        .join(PlanTask, PlanTask.plan_item_id == PlanItem.id)
        .join(PlanSubTask, PlanSubTask.task_id == PlanTask.id)
        .filter(PlanSubTask.segment_ids.any(segment_id))
        .filter(PlanSubTask.deleted_at.is_(None))
        .order_by(PlanItem.day_number.asc(), PlanTask.display_order.asc())
        .limit(1)
        .scalar()
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


def reorder_plan_videos(db: Session, plan_id: UUID, order_by_id: dict) -> None:
    videos = db.query(PlanVideo).filter(PlanVideo.plan_id == plan_id).all()
    for video in videos:
        if video.id in order_by_id:
            video.display_order = order_by_id[video.id]
    db.commit()
