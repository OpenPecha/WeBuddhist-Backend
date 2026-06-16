from typing import Optional, List
from uuid import UUID, uuid4
import logging

from fastapi import HTTPException
from starlette import status
from ..db.database import SessionLocal
from ..users.users_service import validate_and_extract_user_details
from ..texts.texts_utils import TextUtils
from .accumulator_repository import (
    get_all_accumulators,
    get_user_accumulators,
    get_preset_by_id,
    add_accumulator,
    commit_accumulator,
    get_accumulator_by_id,
    get_accumulator_with_history,
    update_accumulator,
    delete_accumulator,
    add_history_row,
    get_user_accumulator_history,
    mantra_exists
)
from .accumulator_response_models import (
    AccumulatorsResponse,
    AccumulatorDTO,
    PublicAccumulatorDTO,
    PublicAccumulatorsResponse,
    CreateAccumulatorRequest,
    UpdateAccumulatorRequest,
    AccumulatorHistoryResponse,
    AccumulatorHistoryDTO,
    AccumulatorSessionDTO
)
from .accumulator_models import Accumulator
from .accumulator_enums import AccumulatorType
from .response_message import (
    NOT_FOUND,
    FORBIDDEN,
    ACCUMULATOR_NOT_FOUND,
    PRESET_NOT_FOUND,
    MANTRA_NOT_FOUND,
    ACCUMULATOR_UPDATE_NOT_ALLOWED,
    ACCUMULATOR_DELETE_NOT_ALLOWED,
    ONLY_USER_ACCUMULATORS_CAN_BE_UPDATED,
    ONLY_USER_ACCUMULATORS_CAN_BE_DELETED
)

logger = logging.getLogger(__name__)


def convert_accumulator_to_dto(accumulator: Accumulator) -> AccumulatorDTO:
    accumulator_type = (
        AccumulatorType(accumulator.type.value)
        if hasattr(accumulator.type, 'value')
        else accumulator.type
    )
    return AccumulatorDTO(
        id=accumulator.id,
        user_id=accumulator.user_id,
        group_id=accumulator.group_id,
        type=accumulator_type,
        name=accumulator.name,
        description=accumulator.description,
        target_count=accumulator.target_count,
        current_count=accumulator.current_count or 0,
        text_id=accumulator.text_id,
        mantra_id=accumulator.mantra_id,
        created_at=accumulator.created_at,
        updated_at=accumulator.updated_at
    )


def convert_accumulators_to_dtos(accumulators: List[Accumulator]) -> List[AccumulatorDTO]:
    return [convert_accumulator_to_dto(accumulator) for accumulator in accumulators]


def convert_accumulator_to_public_dto(accumulator: Accumulator) -> PublicAccumulatorDTO:
    accumulator_type = (
        AccumulatorType(accumulator.type.value)
        if hasattr(accumulator.type, 'value')
        else accumulator.type
    )
    return PublicAccumulatorDTO(
        id=accumulator.id,
        group_id=accumulator.group_id,
        type=accumulator_type,
        name=accumulator.name,
        description=accumulator.description,
        target_count=accumulator.target_count,
        current_count=accumulator.current_count or 0,
        text_id=accumulator.text_id,
        mantra_id=accumulator.mantra_id,
        created_at=accumulator.created_at,
        updated_at=accumulator.updated_at
    )


def validate_mantra_exists(db, mantra_id: UUID) -> None:
    if not mantra_exists(db, mantra_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": NOT_FOUND, "message": MANTRA_NOT_FOUND}
        )


def is_user_created_accumulator(accumulator: Accumulator) -> bool:
    accumulator_type = accumulator.type.value if hasattr(accumulator.type, 'value') else accumulator.type
    return accumulator_type == AccumulatorType.USER.value


def get_all_accumulators_service(
    skip: int = 0,
    limit: int = 20
) -> PublicAccumulatorsResponse:
    with SessionLocal() as db:
        accumulators, total = get_all_accumulators(db, skip, limit)
        return PublicAccumulatorsResponse(
            accumulators=[convert_accumulator_to_public_dto(a) for a in accumulators],
            total=total,
            skip=skip,
            limit=limit
        )


def get_user_accumulators_service(
    user_id: UUID,
    skip: int = 0,
    limit: int = 20
) -> AccumulatorsResponse:
    with SessionLocal() as db:
        accumulators, total = get_user_accumulators(db, user_id, skip, limit)
        return AccumulatorsResponse(
            accumulators=convert_accumulators_to_dtos(accumulators),
            total=total,
            skip=skip,
            limit=limit
        )


def create_accumulator_service(token: str, request: CreateAccumulatorRequest) -> AccumulatorDTO:
    """Create a user accumulator from a preset the user tapped. The preset's
    fields are copied into a new user-owned row; count starts at 0 (the PUT
    endpoint handles counting)."""
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        preset = get_preset_by_id(db, request.preset_id)
        if preset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": NOT_FOUND, "message": PRESET_NOT_FOUND}
            )

        new_accumulator = Accumulator(
            id=uuid4(),
            user_id=current_user.id,
            group_id=preset.group_id,
            type=AccumulatorType.USER,
            name=preset.name,
            description=preset.description,
            target_count=preset.target_count,
            current_count=0,
            text_id=preset.text_id,
            mantra_id=preset.mantra_id
        )

        add_accumulator(db, new_accumulator)
        saved_accumulator = commit_accumulator(db, new_accumulator)
        return convert_accumulator_to_dto(saved_accumulator)


async def update_accumulator_service(token: str, accumulator_id: UUID, request: UpdateAccumulatorRequest) -> AccumulatorDTO:
    current_user = validate_and_extract_user_details(token=token)

    if request.text_id is not None:
        await TextUtils.validate_text_exists(text_id=str(request.text_id))

    with SessionLocal() as db:
        accumulator = get_accumulator_by_id(db, accumulator_id)

        if not accumulator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": NOT_FOUND, "message": ACCUMULATOR_NOT_FOUND}
            )

        if accumulator.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": FORBIDDEN, "message": ACCUMULATOR_UPDATE_NOT_ALLOWED}
            )

        if not is_user_created_accumulator(accumulator):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": FORBIDDEN, "message": ONLY_USER_ACCUMULATORS_CAN_BE_UPDATED}
            )

        if request.name is not None:
            accumulator.name = request.name
        if request.description is not None:
            accumulator.description = request.description
        if request.target_count is not None:
            accumulator.target_count = request.target_count
        if request.text_id is not None:
            accumulator.text_id = request.text_id
        if request.mantra_id is not None:
            validate_mantra_exists(db, request.mantra_id)
            accumulator.mantra_id = request.mantra_id
        if request.current_count is not None:
            delta = request.current_count - (accumulator.current_count or 0)
            accumulator.current_count = request.current_count
            if delta > 0:
                add_history_row(
                    db=db,
                    accumulator_id=accumulator.id,
                    user_id=current_user.id,
                    count=delta
                )

        updated_accumulator = update_accumulator(db, accumulator)
        return convert_accumulator_to_dto(updated_accumulator)


def delete_accumulator_service(token: str, accumulator_id: UUID) -> None:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        accumulator = get_accumulator_by_id(db, accumulator_id)

        if not accumulator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": NOT_FOUND, "message": ACCUMULATOR_NOT_FOUND}
            )

        if accumulator.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": FORBIDDEN, "message": ACCUMULATOR_DELETE_NOT_ALLOWED}
            )

        if not is_user_created_accumulator(accumulator):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": FORBIDDEN, "message": ONLY_USER_ACCUMULATORS_CAN_BE_DELETED}
            )

        delete_accumulator(db, accumulator)


def get_accumulator_detail_service(
    token: str,
    accumulator_id: UUID
) -> AccumulatorHistoryDTO:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        result = get_accumulator_with_history(db, accumulator_id, current_user.id)

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": NOT_FOUND, "message": ACCUMULATOR_NOT_FOUND}
            )

        accumulator, total_counted, sessions = result
        return AccumulatorHistoryDTO(
            accumulator_id=accumulator.id,
            name=accumulator.name,
            description=accumulator.description,
            target_count=accumulator.target_count,
            current_count=accumulator.current_count or 0,
            total_counted=total_counted,
            sessions=[
                AccumulatorSessionDTO(
                    count=session.count,
                    created_at=session.created_at
                )
                for session in sessions
            ]
        )


def get_accumulator_history_service(
    token: str,
    skip: int = 0,
    limit: int = 20
) -> AccumulatorHistoryResponse:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        history_data, total = get_user_accumulator_history(db, current_user.id, skip, limit)

        accumulators = []
        for accumulator, total_counted, sessions in history_data:
            accumulator_history_dto = AccumulatorHistoryDTO(
                accumulator_id=accumulator.id,
                name=accumulator.name,
                description=accumulator.description,
                target_count=accumulator.target_count,
                current_count=accumulator.current_count or 0,
                total_counted=total_counted,
                sessions=[
                    AccumulatorSessionDTO(
                        count=session.count,
                        created_at=session.created_at
                    )
                    for session in sessions
                ]
            )
            accumulators.append(accumulator_history_dto)

        return AccumulatorHistoryResponse(
            accumulators=accumulators,
            total=total,
            skip=skip,
            limit=limit
        )
