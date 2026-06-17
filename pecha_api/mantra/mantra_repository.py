from sqlalchemy import select, exists
from sqlalchemy.orm import Session, selectinload
from typing import Dict, List, Optional
from uuid import UUID

from .mantra_model import Mantra
from .mantra_metadata_model import MantraMetadata


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
