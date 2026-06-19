from uuid import UUID
from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details
from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_repository import get_sub_task_by_subtask_id
from pecha_api.plans.tasks.sub_tasks.subtask_preset_models import SubTaskPreset
from pecha_api.plans.tasks.sub_tasks.subtask_preset_repository import (
    create_preset,
    get_preset_by_subtask_id,
    update_preset,
    delete_preset,
)
from pecha_api.plans.tasks.sub_tasks.subtask_preset_response_models import (
    PresetRequest,
    PresetResponse,
)
from pecha_api.error_contants import ErrorConstants
from pecha_api.utils import Utils


async def create_or_update_preset_service(
    token: str, subtask_id: UUID, preset_request: PresetRequest
) -> PresetResponse:
    current_author = validate_and_extract_author_details(token=token)

    with SessionLocal() as db:
        subtask = get_sub_task_by_subtask_id(db=db, id=subtask_id)
        if not subtask:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subtask not found"
            )

        existing_preset = get_preset_by_subtask_id(db=db, subtask_id=subtask_id)

        if existing_preset:
            existing_preset.version_id = UUID(preset_request.version_id)
            existing_preset.language = preset_request.language
            existing_preset.updated_at = Utils.get_utc_date_time()
            existing_preset.updated_by = current_author.email
            updated = update_preset(db=db, preset=existing_preset)
            return _map_to_response(updated)
        else:
            new_preset = SubTaskPreset(
                subtask_id=subtask_id,
                version_id=UUID(preset_request.version_id),
                language=preset_request.language,
                created_by=current_author.email,
            )
            created = create_preset(db=db, preset=new_preset)
            return _map_to_response(created)


async def get_preset_service(subtask_id: UUID) -> PresetResponse:
    with SessionLocal() as db:
        preset = get_preset_by_subtask_id(db=db, subtask_id=subtask_id)
        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preset not found for this subtask"
            )
        return _map_to_response(preset)


async def delete_preset_service(token: str, subtask_id: UUID) -> None:
    current_author = validate_and_extract_author_details(token=token)

    with SessionLocal() as db:
        preset = get_preset_by_subtask_id(db=db, subtask_id=subtask_id)
        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preset not found for this subtask"
            )
        delete_preset(db=db, preset=preset)


def _map_to_response(preset: SubTaskPreset) -> PresetResponse:
    return PresetResponse(
        id=str(preset.id),
        subtask_id=str(preset.subtask_id),
        version_id=str(preset.version_id),
        language=preset.language,
        created_at=preset.created_at.isoformat(),
        created_by=preset.created_by,
        updated_at=preset.updated_at.isoformat() if preset.updated_at else None,
        updated_by=preset.updated_by,
    )
