from typing import Optional

from ..db.database import SessionLocal
from .mantra_repository import get_all_mantras
from .mantra_response_models import MantraDTO, MantraResponse


def get_mantras_service(language: Optional[str] = None) -> MantraResponse:

    with SessionLocal() as db:
        mantras = get_all_mantras(db, language=language)

        return MantraResponse(
            mantras=[MantraDTO.model_validate(mantra) for mantra in mantras]
        )
