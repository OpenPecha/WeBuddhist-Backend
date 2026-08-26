from typing import Optional

from fastapi import HTTPException
from starlette import status

from ..accumulator.accumulator_repository import get_mala_image_by_id
from ..accumulator.accumulator_service import generate_mala_image_presigned_url
from ..db.database import SessionLocal
from ..plans.authors.plan_authors_service import validate_cms_author_details
from .mantra_model import Mantra
from .mantra_repository import get_all_mantras, save_mantra
from pecha_api.region_restrictions.region_restriction_enums import RestrictedItemType
from pecha_api.region_restrictions.region_restriction_service import filter_items_for_timezone
from .mantra_response_models import (
    CreateMantraRequest,
    MantraDTO,
    MantraMetadataDTO,
    MantraResponse,
)


def _build_mantra_dto(mantra, language: Optional[str]) -> MantraDTO:
    entries = mantra.metadata_entries
    if language:
        language_upper = language.upper()
        entries = [
            entry for entry in entries
            if entry.language.value == language_upper
        ]
    mala = mantra.mala
    return MantraDTO(
        id=mantra.id,
        audio_url=mantra.audio_url,
        mala_image_id=mala.id if mala is not None else None,
        mala_image_url=generate_mala_image_presigned_url(mala.url) if mala is not None else None,
        metadata=[MantraMetadataDTO.model_validate(entry) for entry in entries],
    )


def get_mantras_service(
    language: Optional[str] = None,
    timezone_name: Optional[str] = None,
) -> MantraResponse:

    with SessionLocal() as db:
        mantras = get_all_mantras(db, language=language)
        visible_mantras = filter_items_for_timezone(
            mantras,
            timezone_name=timezone_name,
            item_type=RestrictedItemType.MANTRA,
            id_of=lambda mantra: mantra.id,
        )

        return MantraResponse(
            mantras=[_build_mantra_dto(mantra, language) for mantra in visible_mantras]
        )


def create_mantra_service(token: str, request: CreateMantraRequest) -> MantraDTO:
    validate_cms_author_details(token=token)

    mantra = Mantra(
        audio_url=request.audio_url,
        mala_image=request.mala_image_id,
    )

    with SessionLocal() as db:
        if request.mala_image_id is not None:
            mala = get_mala_image_by_id(db, request.mala_image_id)
            if mala is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Mala image with id '{request.mala_image_id}' does not exist",
                )

        saved = save_mantra(db, mantra, request.metadata)
        return _build_mantra_dto(saved, language=None)
