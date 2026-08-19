from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from .subtask_preset_models import SubTaskPreset


def create_preset(db: Session, preset: SubTaskPreset) -> SubTaskPreset:
    db.add(preset)
    db.commit()
    db.refresh(preset)
    return preset


def get_preset_by_subtask_id(db: Session, subtask_id: UUID) -> Optional[SubTaskPreset]:
    return db.query(SubTaskPreset).filter(SubTaskPreset.subtask_id == subtask_id).first()


def update_preset(db: Session, preset: SubTaskPreset) -> SubTaskPreset:
    db.commit()
    db.refresh(preset)
    return preset


def delete_preset(db: Session, preset: SubTaskPreset) -> None:
    db.delete(preset)
    db.commit()
