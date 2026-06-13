from typing import Optional

from ..db.database import SessionLocal
from .mantra_repository import get_all_mantras
from .mantra_response_models import MantraDTO, MantraMetadataDTO, MantraResponse


def _build_mantra_dto(mantra, language: Optional[str]) -> MantraDTO:
    entries = mantra.metadata_entries
    if language:
        language_upper = language.upper()
        entries = [
            entry for entry in entries
            if entry.language.value == language_upper
        ]
    return MantraDTO(
        id=mantra.id,
        audio_url=mantra.audio_url,
        metadata=[MantraMetadataDTO.model_validate(entry) for entry in entries],
    )


def get_mantras_service(language: Optional[str] = None) -> MantraResponse:

    with SessionLocal() as db:
        mantras = get_all_mantras(db, language=language)

        return MantraResponse(
            mantras=[_build_mantra_dto(mantra, language) for mantra in mantras]
        )
