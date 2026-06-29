from typing import List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from pecha_api.plans.videos.plan_video_models import PlanVideo


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
