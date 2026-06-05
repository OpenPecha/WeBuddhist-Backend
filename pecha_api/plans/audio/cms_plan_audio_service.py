import os
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.config import get
from pecha_api.db.database import SessionLocal
from pecha_api.plans.audio.plan_audio_response_models import PlanAudioDTO, PlanAudioListResponse
from pecha_api.plans.audio.plan_item_audio_repository import get_plan_item_audio_paginated
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.authors.plan_authors_service import validate_cms_author_details
from pecha_api.plans.cms.cms_plans_repository import get_plan_by_id
from pecha_api.plans.groups.groups_repository import get_author_group_ids
from pecha_api.plans.response_message import BAD_REQUEST, PLAN_NOT_FOUND
from pecha_api.plans.shared.permissions import is_reviewer, is_super_admin, require_can_read_group_content
from pecha_api.uploads.S3_utils import generate_presigned_access_url


def _audio_file_name(audio_key: str) -> str:
    return os.path.basename(audio_key)


def get_cms_plan_audio_list(
    token: str,
    search: Optional[str],
    plan_id: Optional[UUID],
    skip: int,
    limit: int,
) -> PlanAudioListResponse:
    current_author = validate_cms_author_details(token=token)
    see_all = is_super_admin(current_author) or is_reviewer(current_author)

    with SessionLocal() as db_session:
        group_ids = None
        if not see_all:
            group_ids = get_author_group_ids(db=db_session, author_id=current_author.id)
        if plan_id is not None:
            plan = get_plan_by_id(db=db_session, plan_id=plan_id)
            if not plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=ResponseError(error=BAD_REQUEST, message=PLAN_NOT_FOUND).model_dump(),
                )
            require_can_read_group_content(
                db=db_session,
                group_id=plan.group_id,
                author=current_author,
            )
        rows, total = get_plan_item_audio_paginated(
            db=db_session,
            search=search,
            plan_id=plan_id,
            group_ids=group_ids,
            see_all=see_all,
            skip=skip,
            limit=limit,
        )

    bucket_name = get("AWS_BUCKET_NAME")
    audio_items: List[PlanAudioDTO] = []
    for audio_row, plan_item, _plan in rows:
        audio_url = generate_presigned_access_url(
            bucket_name=bucket_name,
            s3_key=audio_row.audio_key,
        )
        audio_items.append(
            PlanAudioDTO(
                id=audio_row.id,
                audio_key=audio_row.audio_key,
                file_name=_audio_file_name(audio_row.audio_key),
                audio_url=audio_url,
                duration_ms=audio_row.duration_ms,
                mime_type=audio_row.mime_type,
                file_size_bytes=audio_row.file_size_bytes,
                plan_item_id=plan_item.id,
                plan_id=plan_item.plan_id,
                day_number=plan_item.day_number,
                created_at=audio_row.created_at,
            )
        )

    return PlanAudioListResponse(
        audio=audio_items,
        skip=skip,
        limit=limit,
        total=total,
    )
