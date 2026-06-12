from typing import Optional, List
from uuid import UUID, uuid4
import logging

from fastapi import HTTPException
from starlette import status
from ..db.database import SessionLocal
from ..users.users_service import validate_and_extract_user_details
from ..texts.texts_utils import TextUtils
from .accumulator_repository import (
    get_accumulators_by_group,
    get_user_accumulators_by_group,
    save_accumulator,
    get_accumulator_by_id,
    update_accumulator,
    delete_accumulator,
    record_accumulator_count,
    get_user_accumulator_history
)
from .accumulator_response_models import (
    AccumulatorsResponse,
    AccumulatorDTO,
    CreateAccumulatorRequest,
    UpdateAccumulatorRequest,
    RecordAccumulatorCountRequest,
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
    ACCUMULATOR_UPDATE_NOT_ALLOWED,
    ACCUMULATOR_DELETE_NOT_ALLOWED,
    ACCUMULATOR_COUNT_NOT_ALLOWED,
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
        created_at=accumulator.created_at,
        updated_at=accumulator.updated_at
    )


def convert_accumulators_to_dtos(accumulators: List[Accumulator]) -> List[AccumulatorDTO]:
    return [convert_accumulator_to_dto(accumulator) for accumulator in accumulators]


def is_user_created_accumulator(accumulator: Accumulator) -> bool:
    accumulator_type = accumulator.type.value if hasattr(accumulator.type, 'value') else accumulator.type
    return accumulator_type == AccumulatorType.USER.value


def get_all_accumulators_service(
    group_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 20
) -> AccumulatorsResponse:
    with SessionLocal() as db:
        accumulators, total = get_accumulators_by_group(db, group_id, skip, limit)
        return AccumulatorsResponse(
            accumulators=convert_accumulators_to_dtos(accumulators),
            total=total,
            skip=skip,
            limit=limit
        )


def get_user_accumulators_service(
    user_id: UUID,
    group_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 20
) -> AccumulatorsResponse:
    with SessionLocal() as db:
        accumulators, total = get_user_accumulators_by_group(db, user_id, group_id, skip, limit)
        return AccumulatorsResponse(
            accumulators=convert_accumulators_to_dtos(accumulators),
            total=total,
            skip=skip,
            limit=limit
        )


async def create_accumulator_service(token: str, request: CreateAccumulatorRequest) -> AccumulatorDTO:
    current_user = validate_and_extract_user_details(token=token)

    if request.text_id is not None:
        await TextUtils.validate_text_exists(text_id=str(request.text_id))

    with SessionLocal() as db:
        new_accumulator = Accumulator(
            id=uuid4(),
            user_id=current_user.id,
            group_id=request.group_id,
            type=AccumulatorType.USER,
            name=request.name,
            description=request.description,
            target_count=request.target_count,
            current_count=0,
            text_id=request.text_id
        )

        saved_accumulator = save_accumulator(db, new_accumulator)
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


def record_accumulator_count_service(token: str, request: RecordAccumulatorCountRequest) -> AccumulatorDTO:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        accumulator = get_accumulator_by_id(db, request.accumulator_id)
        if not accumulator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": NOT_FOUND, "message": ACCUMULATOR_NOT_FOUND}
            )

        if accumulator.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": FORBIDDEN, "message": ACCUMULATOR_COUNT_NOT_ALLOWED}
            )

        updated_accumulator = record_accumulator_count(
            db=db,
            accumulator=accumulator,
            user_id=current_user.id,
            count=request.count
        )
        return convert_accumulator_to_dto(updated_accumulator)


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
