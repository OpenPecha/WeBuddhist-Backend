from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from pecha_api.plans.audio.sub_task_timestamps_models import SubTaskTimestamp


def get_sub_task_timestamp_by_sub_task_id(
    db: Session, sub_task_id: UUID
) -> Optional[SubTaskTimestamp]:
    return (
        db.query(SubTaskTimestamp)
        .filter(SubTaskTimestamp.sub_task_id == sub_task_id)
        .first()
    )


def upsert_sub_task_timestamp(
    db: Session,
    sub_task_id: UUID,
    start_ms: int,
    end_ms: int,
    created_by: str,
) -> SubTaskTimestamp:
    existing = get_sub_task_timestamp_by_sub_task_id(db=db, sub_task_id=sub_task_id)
    if existing:
        existing.start_ms = start_ms
        existing.end_ms = end_ms
        existing.updated_by = created_by
        db.commit()
        db.refresh(existing)
        return existing
    row = SubTaskTimestamp(
        sub_task_id=sub_task_id,
        start_ms=start_ms,
        end_ms=end_ms,
        created_by=created_by,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete_sub_task_timestamp(db: Session, sub_task_id: UUID) -> None:
    db.query(SubTaskTimestamp).filter(SubTaskTimestamp.sub_task_id == sub_task_id).delete()
    db.commit()
