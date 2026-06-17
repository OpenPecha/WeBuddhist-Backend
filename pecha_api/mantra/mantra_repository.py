from fastapi import HTTPException
from sqlalchemy import select, exists
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from starlette import status
from typing import Dict, List, Optional
from uuid import UUID

from .mantra_model import Mantra
from .mantra_metadata_model import MantraMetadata


def _persist_metadata_entries(db: Session, mantra_id: UUID, metadata_entries: List) -> None:
    for entry in metadata_entries:
        db.add(
            MantraMetadata(
                mantra_id=mantra_id,
                mantra=entry.mantra,
                title=entry.title,
                pronunciation=entry.pronunciation,
                language=entry.language,
            )
        )


def save_mantra(db: Session, mantra: Mantra, metadata_entries: List) -> Mantra:
    try:
        db.add(mantra)
        db.flush()
        _persist_metadata_entries(db, mantra.id, metadata_entries)
        db.commit()
        db.refresh(mantra)
        return get_mantra_by_id(db, mantra.id)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "BAD_REQUEST", "message": str(exc.orig)},
        ) from exc


def get_mantra_by_id(db: Session, mantra_id: UUID) -> Optional[Mantra]:
    return (
        db.query(Mantra)
        .options(
            selectinload(Mantra.metadata_entries),
            selectinload(Mantra.mala),
        )
        .filter(Mantra.id == mantra_id)
        .first()
    )


def get_all_mantras(db: Session, language: Optional[str] = None) -> List[Mantra]:

    query = db.query(Mantra).options(selectinload(Mantra.metadata_entries))

    if language:
        language_upper = language.upper()
        query = query.filter(
            exists(
                select(1).where(
                    MantraMetadata.mantra_id == Mantra.id,
                    MantraMetadata.language == language_upper,
                )
            )
        )

    return query.all()


def get_mantras_by_ids(db: Session, mantra_ids: List[UUID]) -> Dict[UUID, Mantra]:
    if not mantra_ids:
        return {}
    mantras = (
        db.query(Mantra)
        .options(
            selectinload(Mantra.metadata_entries),
            selectinload(Mantra.mala),
        )
        .filter(Mantra.id.in_(mantra_ids))
        .all()
    )
    return {mantra.id: mantra for mantra in mantras}
