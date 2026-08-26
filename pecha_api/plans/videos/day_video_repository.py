from typing import List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from pecha_api.plans.videos.day_video_models import DayVideo


def get_day_videos_by_day_id(db: Session, day_id: UUID) -> List[DayVideo]:
    return (
        db.query(DayVideo)
        .filter(DayVideo.day_id == day_id)
        .order_by(DayVideo.display_order.asc(), DayVideo.created_at.asc())
        .all()
    )


def get_day_videos_by_day_ids(db: Session, day_ids: List[UUID]) -> List[DayVideo]:
    if not day_ids:
        return []
    return (
        db.query(DayVideo)
        .filter(DayVideo.day_id.in_(day_ids))
        .order_by(DayVideo.display_order.asc(), DayVideo.created_at.asc())
        .all()
    )


def get_day_video_by_id(db: Session, day_id: UUID, video_id: UUID) -> Optional[DayVideo]:
    return (
        db.query(DayVideo)
        .filter(DayVideo.id == video_id, DayVideo.day_id == day_id)
        .first()
    )


def get_next_display_order(db: Session, day_id: UUID) -> int:
    current_max = (
        db.query(func.max(DayVideo.display_order))
        .filter(DayVideo.day_id == day_id)
        .scalar()
    )
    return 0 if current_max is None else current_max + 1


def create_day_video(db: Session, day_video: DayVideo) -> DayVideo:
    db.add(day_video)
    db.commit()
    db.refresh(day_video)
    return day_video


def update_day_video(db: Session, day_video: DayVideo) -> DayVideo:
    db.commit()
    db.refresh(day_video)
    return day_video


def delete_day_video(db: Session, day_id: UUID, video_id: UUID) -> None:
    db.query(DayVideo).filter(
        DayVideo.id == video_id, DayVideo.day_id == day_id
    ).delete()
    db.commit()


def reorder_day_videos(db: Session, day_id: UUID, order_by_id: dict) -> None:
    videos = db.query(DayVideo).filter(DayVideo.day_id == day_id).all()
    for video in videos:
        if video.id in order_by_id:
            video.display_order = order_by_id[video.id]
    db.commit()
