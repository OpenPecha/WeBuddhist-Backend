from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from pecha_api.plans.audio.plan_item_audio_models import PlanItemAudio
from pecha_api.plans.items.plan_items_models import PlanItem
from pecha_api.plans.plans_models import Plan


def get_plan_item_audio_paginated(
    db: Session,
    *,
    search: Optional[str],
    plan_id: Optional[UUID],
    group_ids: Optional[List[UUID]] = None,
    see_all: bool = False,
    skip: int,
    limit: int,
) -> Tuple[List[Tuple[PlanItemAudio, PlanItem, Plan]], int]:
    query = (
        db.query(PlanItemAudio, PlanItem, Plan)
        .join(PlanItem, PlanItem.id == PlanItemAudio.plan_item_id)
        .join(Plan, Plan.id == PlanItem.plan_id)
        .filter(Plan.deleted_at.is_(None))
    )
    if not see_all and group_ids is not None:
        if not group_ids:
            return [], 0
        query = query.filter(Plan.group_id.in_(group_ids))
    if plan_id is not None:
        query = query.filter(Plan.id == plan_id)
    if search:
        query = query.filter(PlanItemAudio.audio_key.ilike(f"%{search}%"))
    total = query.count()
    rows = (
        query.order_by(PlanItemAudio.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rows, total


def get_accessible_plan_item_audio_by_key(
    db: Session,
    audio_key: str,
    group_ids: Optional[List[UUID]] = None,
    see_all: bool = False,
) -> Optional[PlanItemAudio]:
    query = (
        db.query(PlanItemAudio)
        .join(PlanItem, PlanItem.id == PlanItemAudio.plan_item_id)
        .join(Plan, Plan.id == PlanItem.plan_id)
        .filter(Plan.deleted_at.is_(None), PlanItemAudio.audio_key == audio_key)
    )
    if not see_all and group_ids is not None:
        if not group_ids:
            return None
        query = query.filter(Plan.group_id.in_(group_ids))
    return query.first()


def count_plan_item_audio_by_audio_key(db: Session, audio_key: str) -> int:
    return db.query(PlanItemAudio).filter(PlanItemAudio.audio_key == audio_key).count()


def get_plan_item_audio_by_plan_item_id(db: Session, plan_item_id: UUID) -> Optional[PlanItemAudio]:
    return (
        db.query(PlanItemAudio)
        .filter(PlanItemAudio.plan_item_id == plan_item_id)
        .first()
    )


def get_plan_item_audio_by_plan_item_ids(
    db: Session, plan_item_ids: List[UUID]
) -> List[PlanItemAudio]:
    if not plan_item_ids:
        return []
    return (
        db.query(PlanItemAudio)
        .filter(PlanItemAudio.plan_item_id.in_(plan_item_ids))
        .all()
    )


def upsert_plan_item_audio(db: Session, plan_item_audio: PlanItemAudio) -> PlanItemAudio:
    existing = get_plan_item_audio_by_plan_item_id(db=db, plan_item_id=plan_item_audio.plan_item_id)
    if existing:
        existing.audio_key = plan_item_audio.audio_key
        existing.duration_ms = plan_item_audio.duration_ms
        existing.mime_type = plan_item_audio.mime_type
        existing.file_size_bytes = plan_item_audio.file_size_bytes
        existing.updated_by = plan_item_audio.updated_by
        db.commit()
        db.refresh(existing)
        return existing
    db.add(plan_item_audio)
    db.commit()
    db.refresh(plan_item_audio)
    return plan_item_audio


def delete_plan_item_audio(db: Session, plan_item_id: UUID) -> None:
    db.query(PlanItemAudio).filter(PlanItemAudio.plan_item_id == plan_item_id).delete()
    db.commit()


def update_plan_item_audio_duration(
    db: Session, plan_item_id: UUID, duration_ms: int, updated_by: str
) -> Optional[PlanItemAudio]:
    existing = get_plan_item_audio_by_plan_item_id(db=db, plan_item_id=plan_item_id)
    if not existing:
        return None
    existing.duration_ms = duration_ms
    existing.updated_by = updated_by
    db.commit()
    db.refresh(existing)
    return existing
