from sqlalchemy.orm import Session
from typing import List, Optional

from .mantra_model import Mantra


def get_all_mantras(db: Session, language: Optional[str] = None) -> List[Mantra]:

    query = db.query(Mantra)

    if language:
        query = query.filter(Mantra.language == language.upper())

    return query.all()


def create_mantra(db: Session, mantra: Mantra) -> Mantra:

    db.add(mantra)
    db.commit()
    db.refresh(mantra)
    return mantra
