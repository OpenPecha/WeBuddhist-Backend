import uuid
from typing import List

from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details
from pecha_api.plans.shared.permissions import require_super_admin

from .id_remap_repository import remap_segment_ids as remap_segment_ids_postgres
from .id_remap_repository import remap_text_ids as remap_text_ids_postgres
from .id_remap_response_models import IdRemapResult, IdRemapSkippedEntry


def _build_result(old_id: str, new_id: str, updated: dict, skipped: List[dict]) -> IdRemapResult:
    return IdRemapResult(
        old_id=old_id,
        new_id=new_id,
        updated_counts=updated,
        skipped=[IdRemapSkippedEntry(**entry) for entry in skipped],
    )


def _run_postgres_remap(remap_fn, **kwargs) -> tuple:
    with SessionLocal() as db:
        try:
            updated, skipped = remap_fn(db=db, **kwargs)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Postgres update failed, no changes were committed: {e}",
            )
    return updated, skipped


async def remap_segment_id(
    token: str,
    old_segment_id: str,
    new_segment_id: str,
) -> IdRemapResult:
    caller = validate_and_extract_author_details(token=token)
    require_super_admin(caller)

    if old_segment_id == new_segment_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="old_segment_id and new_segment_id must differ",
        )

    updated, skipped = _run_postgres_remap(
        remap_segment_ids_postgres,
        old_segment_id=old_segment_id,
        new_segment_id=new_segment_id,
    )

    return _build_result(old_id=old_segment_id, new_id=new_segment_id, updated=updated, skipped=skipped)


async def remap_text_id(
    token: str,
    old_text_id: str,
    new_text_id: str,
) -> IdRemapResult:
    caller = validate_and_extract_author_details(token=token)
    require_super_admin(caller)

    if old_text_id == new_text_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="old_text_id and new_text_id must differ",
        )

    try:
        uuid.UUID(old_text_id)
        uuid.UUID(new_text_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="old_text_id and new_text_id must be valid UUIDs",
        )

    updated, skipped = _run_postgres_remap(
        remap_text_ids_postgres,
        old_text_id=old_text_id,
        new_text_id=new_text_id,
    )

    return _build_result(old_id=old_text_id, new_id=new_text_id, updated=updated, skipped=skipped)
