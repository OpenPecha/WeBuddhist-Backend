from sqlalchemy import select, exists
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional

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
