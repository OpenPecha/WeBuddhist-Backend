from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.accumulator.accumulator_service import (
    _pick_mantra_metadata,
    generate_mala_image_presigned_url,
)
from pecha_api.accumulator.response_message import MANTRA_NOT_FOUND, NOT_FOUND
from pecha_api.db.database import SessionLocal
from pecha_api.mantra.mantra_count_repository import (
    get_user_mantra_count_for_mantra,
    get_user_mantra_counts,
)
from pecha_api.mantra.mantra_count_response_models import (
    MantraCountDetailDTO,
    MantraCountSummaryDTO,
    MantraCountsResponse,
)
from pecha_api.mantra.mantra_repository import get_mantra_by_id, get_mantras_by_ids
from pecha_api.users.users_service import validate_and_extract_user_details


def _resolve_mantra_title(mantra, language: Optional[str]) -> Optional[str]:
    if mantra is None:
        return None
    metadata = _pick_mantra_metadata(mantra.metadata_entries, language)
    if metadata is None:
        return None
    return metadata.title


def _resolve_mala_image_fields(mantra) -> tuple[Optional[UUID], Optional[str]]:
    if mantra is None:
        return None, None
    mala = mantra.mala
    if mala is None:
        return None, None
    return mala.id, generate_mala_image_presigned_url(mala.url)


def _build_count_fields(total_count: int) -> dict:
    return {
        "private_count": total_count,
        "allocated_count": 0,
        "total_count": total_count,
    }


def get_user_mantra_counts_service(
    token: str,
    language: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> MantraCountsResponse:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        rows, total = get_user_mantra_counts(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
        )
        mantras_by_id = get_mantras_by_ids(db, [row.mantra_id for row in rows])

        counts = []
        for row in rows:
            mantra = mantras_by_id.get(row.mantra_id)
            mala_image_id, mala_image_url = _resolve_mala_image_fields(mantra)
            counts.append(
                MantraCountSummaryDTO(
                    mantra_id=row.mantra_id,
                    mantra_title=_resolve_mantra_title(mantra, language),
                    mala_image_id=mala_image_id,
                    mala_image_url=mala_image_url,
                    updated_at=row.updated_at,
                    **_build_count_fields(row.total_count),
                )
            )

        return MantraCountsResponse(
            counts=counts,
            total=total,
            skip=skip,
            limit=limit,
        )


def get_user_mantra_count_detail_service(
    token: str,
    mantra_id: UUID,
    language: Optional[str] = None,
) -> MantraCountDetailDTO:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        mantra = get_mantra_by_id(db, mantra_id)
        if mantra is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": NOT_FOUND, "message": MANTRA_NOT_FOUND},
            )

        total_count, updated_at = get_user_mantra_count_for_mantra(
            db=db,
            user_id=current_user.id,
            mantra_id=mantra_id,
        )

        return MantraCountDetailDTO(
            mantra_id=mantra_id,
            mantra_title=_resolve_mantra_title(mantra, language),
            allocations=[],
            updated_at=updated_at,
            **_build_count_fields(total_count),
        )
