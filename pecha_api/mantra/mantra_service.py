from typing import Optional

from ..db.database import SessionLocal
from .mantra_repository import get_all_mantras, create_mantra
from .mantra_response_models import MantraDTO, MantraResponse, CreateMantraRequest
from .mantra_model import Mantra


def get_mantras_service(language: Optional[str] = None) -> MantraResponse:

    with SessionLocal() as db:
        mantras = get_all_mantras(db, language=language)

        return MantraResponse(
            mantras=[MantraDTO.model_validate(mantra) for mantra in mantras]
        )


def create_mantra_service(request: CreateMantraRequest) -> MantraDTO:

    with SessionLocal() as db:
        mantra = Mantra(
            audio_url=request.audio_url,
            text=request.text,
            meaning=request.meaning,
            language=request.language
        )

        created = create_mantra(db, mantra)

        return MantraDTO.model_validate(created)
