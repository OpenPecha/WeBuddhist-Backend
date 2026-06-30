from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.users.users_service import validate_and_extract_user_details
from pecha_api.plans.authors.plan_authors_service import validate_cms_author_details
from pecha_api.plans.shared.permissions import (
    require_can_create_content,
    require_can_read_group_content,
    require_can_change_status,
)
from pecha_api.plans.groups.groups_repository import is_user_joined_group
from .group_accumulator_repository import (
    create_group_accumulator,
    get_group_accumulators,
    get_group_accumulator_by_id,
    update_group_accumulator,
    delete_group_accumulator,
    add_group_history_row,
    get_group_accumulator_history,
    get_group_accumulator_total_count,
    get_user_group_accumulator_count,
    verify_group_exists,
)
from .group_accumulator_response_models import (
    CreateGroupAccumulatorRequest,
    UpdateGroupAccumulatorRequest,
    GroupAccumulatorDTO,
    GroupAccumulatorsResponse,
    SubmitGroupCountRequest,
    GroupAccumulatorDetailDTO,
    GroupAccumulatorHistoryResponse,
    GroupAccumulatorHistoryItemDTO,
)


def _convert_to_dto(group_accumulator) -> GroupAccumulatorDTO:
    return GroupAccumulatorDTO(
        id=group_accumulator.id,
        accumulator_id=group_accumulator.accumulator_id,
        group_id=group_accumulator.group_id,
        title=group_accumulator.title,
        target_count=group_accumulator.target_count,
        start_date=group_accumulator.start_date,
        end_date=group_accumulator.end_date,
        created_at=group_accumulator.created_at,
        updated_at=group_accumulator.updated_at,
    )


def create_group_accumulator_service(
    group_id: UUID,
    request: CreateGroupAccumulatorRequest,
) -> GroupAccumulatorDTO:
    with SessionLocal() as db:
        if not verify_group_exists(db, group_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NOT_FOUND", "message": "Group not found"}
            )
        
        group_accumulator = create_group_accumulator(
            db=db,
            group_id=group_id,
            accumulator_id=request.accumulator_id,
            title=request.title,
            target_count=request.target_count,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        return _convert_to_dto(group_accumulator)


def get_group_accumulators_service(
    group_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> GroupAccumulatorsResponse:
    with SessionLocal() as db:
        accumulators, total = get_group_accumulators(db, group_id, skip, limit)
        return GroupAccumulatorsResponse(
            accumulators=[_convert_to_dto(acc) for acc in accumulators],
            total=total,
            skip=skip,
            limit=limit,
        )


def get_group_accumulator_service(
    group_accumulator_id: UUID,
) -> GroupAccumulatorDetailDTO:
    with SessionLocal() as db:
        group_accumulator = get_group_accumulator_by_id(db, group_accumulator_id)
        if not group_accumulator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NOT_FOUND", "message": "Group accumulator not found"}
            )
        
        total_count = get_group_accumulator_total_count(db, group_accumulator_id)
        
        return GroupAccumulatorDetailDTO(
            id=group_accumulator.id,
            accumulator_id=group_accumulator.accumulator_id,
            group_id=group_accumulator.group_id,
            title=group_accumulator.title,
            target_count=group_accumulator.target_count,
            start_date=group_accumulator.start_date,
            end_date=group_accumulator.end_date,
            total_count=total_count,
            created_at=group_accumulator.created_at,
            updated_at=group_accumulator.updated_at,
        )


def update_group_accumulator_service(
    group_id: UUID,
    group_accumulator_id: UUID,
    request: UpdateGroupAccumulatorRequest,
) -> GroupAccumulatorDTO:
    with SessionLocal() as db:
        group_accumulator = get_group_accumulator_by_id(db, group_accumulator_id)
        if not group_accumulator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NOT_FOUND", "message": "Group accumulator not found"}
            )
        
        if group_accumulator.group_id != group_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "FORBIDDEN", "message": "Group accumulator does not belong to this group"}
            )
        
        if request.accumulator_id is not None:
            group_accumulator.accumulator_id = request.accumulator_id
        if request.title is not None:
            group_accumulator.title = request.title
        if request.target_count is not None:
            group_accumulator.target_count = request.target_count
        if request.start_date is not None:
            group_accumulator.start_date = request.start_date
        if request.end_date is not None:
            group_accumulator.end_date = request.end_date
        
        updated = update_group_accumulator(db, group_accumulator)
        return _convert_to_dto(updated)


def delete_group_accumulator_service(
    group_id: UUID,
    group_accumulator_id: UUID,
) -> None:
    with SessionLocal() as db:
        group_accumulator = get_group_accumulator_by_id(db, group_accumulator_id)
        if not group_accumulator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NOT_FOUND", "message": "Group accumulator not found"}
            )
        
        if group_accumulator.group_id != group_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "FORBIDDEN", "message": "Group accumulator does not belong to this group"}
            )
        
        delete_group_accumulator(db, group_accumulator)


def delete_group_accumulator_user_service(
    token: str,
    group_id: UUID,
    group_accumulator_id: UUID,
) -> None:
    """Delete a group accumulator (User - requires group membership)."""
    current_user = validate_and_extract_user_details(token=token)
    
    with SessionLocal() as db:
        # Verify user is a member of the group
        if not is_user_joined_group(db=db, group_id=group_id, user_id=current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "FORBIDDEN", "message": "You must be a member of this group"}
            )
        
        group_accumulator = get_group_accumulator_by_id(db, group_accumulator_id)
        if not group_accumulator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NOT_FOUND", "message": "Group accumulator not found"}
            )
        
        if group_accumulator.group_id != group_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "FORBIDDEN", "message": "Group accumulator does not belong to this group"}
            )
        
        delete_group_accumulator(db, group_accumulator)


def submit_group_count_service(
    token: str,
    group_accumulator_id: UUID,
    request: SubmitGroupCountRequest,
) -> tuple[GroupAccumulatorHistoryItemDTO, bool]:
    """
    Submit a count contribution to a group accumulator.
    
    Returns:
        tuple: (history_item_dto, is_created) where is_created indicates if a new history entry was created
    """
    current_user = validate_and_extract_user_details(token=token)
    
    with SessionLocal() as db:
        group_accumulator = get_group_accumulator_by_id(db, group_accumulator_id)
        if not group_accumulator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NOT_FOUND", "message": "Group accumulator not found"}
            )
        
        # Verify user is a member of the group
        if not is_user_joined_group(db=db, group_id=group_accumulator.group_id, user_id=current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "FORBIDDEN", "message": "You must be a member of this group"}
            )
        
        # Get user's current total count
        user_current_count = get_user_group_accumulator_count(
            db=db,
            group_accumulator_id=group_accumulator_id,
            user_id=current_user.id
        )
        
        # Calculate delta
        delta = request.current_count - user_current_count
        
        # Only record history if delta is positive
        if delta > 0:
            history = add_group_history_row(
                db=db,
                group_accumulator_id=group_accumulator_id,
                user_id=current_user.id,
                count=delta,
            )
            
            return (
                GroupAccumulatorHistoryItemDTO(
                    id=history.id,
                    user_id=history.user_id,
                    count=history.count,
                    created_at=history.created_at,
                ),
                True,  # is_created
            )
        
        # Return a response with zero count if no change or decrease
        # id is None to indicate no history entry was created
        return (
            GroupAccumulatorHistoryItemDTO(
                id=None,
                user_id=current_user.id,
                count=0,
                created_at=group_accumulator.created_at,
            ),
            False,  # is_created
        )


def get_group_accumulator_history_service(
    group_accumulator_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> GroupAccumulatorHistoryResponse:
    with SessionLocal() as db:
        group_accumulator = get_group_accumulator_by_id(db, group_accumulator_id)
        if not group_accumulator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NOT_FOUND", "message": "Group accumulator not found"}
            )
        
        history, total = get_group_accumulator_history(db, group_accumulator_id, skip, limit)
        total_count = get_group_accumulator_total_count(db, group_accumulator_id)
        
        return GroupAccumulatorHistoryResponse(
            group_accumulator=GroupAccumulatorDetailDTO(
                id=group_accumulator.id,
                accumulator_id=group_accumulator.accumulator_id,
                group_id=group_accumulator.group_id,
                title=group_accumulator.title,
                target_count=group_accumulator.target_count,
                start_date=group_accumulator.start_date,
                end_date=group_accumulator.end_date,
                total_count=total_count,
                created_at=group_accumulator.created_at,
                updated_at=group_accumulator.updated_at,
            ),
            history=[
                GroupAccumulatorHistoryItemDTO(
                    id=h.id,
                    user_id=h.user_id,
                    count=h.count,
                    created_at=h.created_at,
                )
                for h in history
            ],
            total=total,
            skip=skip,
            limit=limit,
        )


# =============================================================================
# CMS Service Functions (with authorization)
# =============================================================================

def create_group_accumulator_cms_service(
    token: str,
    group_id: UUID,
    request: CreateGroupAccumulatorRequest,
) -> GroupAccumulatorDTO:
    """Create a group accumulator (CMS - requires author with create permission)."""
    author = validate_cms_author_details(token=token)
    with SessionLocal() as db:
        require_can_create_content(db=db, group_id=group_id, author=author)
        
        if not verify_group_exists(db, group_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NOT_FOUND", "message": "Group not found"}
            )
        
        group_accumulator = create_group_accumulator(
            db=db,
            group_id=group_id,
            accumulator_id=request.accumulator_id,
            title=request.title,
            target_count=request.target_count,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        return _convert_to_dto(group_accumulator)


def get_group_accumulators_cms_service(
    token: str,
    group_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> GroupAccumulatorsResponse:
    """List group accumulators (CMS - requires author with read permission)."""
    author = validate_cms_author_details(token=token)
    with SessionLocal() as db:
        require_can_read_group_content(db=db, group_id=group_id, author=author)
        accumulators, total = get_group_accumulators(db, group_id, skip, limit)
        return GroupAccumulatorsResponse(
            accumulators=[_convert_to_dto(acc) for acc in accumulators],
            total=total,
            skip=skip,
            limit=limit,
        )


def get_group_accumulator_cms_service(
    token: str,
    group_id: UUID,
    group_accumulator_id: UUID,
) -> GroupAccumulatorDetailDTO:
    """Get a single group accumulator (CMS - requires author with read permission)."""
    author = validate_cms_author_details(token=token)
    with SessionLocal() as db:
        require_can_read_group_content(db=db, group_id=group_id, author=author)
        
        group_accumulator = get_group_accumulator_by_id(db, group_accumulator_id)
        if not group_accumulator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NOT_FOUND", "message": "Group accumulator not found"}
            )
        
        if group_accumulator.group_id != group_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "FORBIDDEN", "message": "Group accumulator does not belong to this group"}
            )
        
        total_count = get_group_accumulator_total_count(db, group_accumulator_id)
        
        return GroupAccumulatorDetailDTO(
            id=group_accumulator.id,
            accumulator_id=group_accumulator.accumulator_id,
            group_id=group_accumulator.group_id,
            title=group_accumulator.title,
            target_count=group_accumulator.target_count,
            start_date=group_accumulator.start_date,
            end_date=group_accumulator.end_date,
            total_count=total_count,
            created_at=group_accumulator.created_at,
            updated_at=group_accumulator.updated_at,
        )


def update_group_accumulator_cms_service(
    token: str,
    group_id: UUID,
    group_accumulator_id: UUID,
    request: UpdateGroupAccumulatorRequest,
) -> GroupAccumulatorDTO:
    """Update a group accumulator (CMS - requires author with status change permission)."""
    author = validate_cms_author_details(token=token)
    with SessionLocal() as db:
        require_can_change_status(db=db, group_id=group_id, author=author)
        
        group_accumulator = get_group_accumulator_by_id(db, group_accumulator_id)
        if not group_accumulator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NOT_FOUND", "message": "Group accumulator not found"}
            )
        
        if group_accumulator.group_id != group_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "FORBIDDEN", "message": "Group accumulator does not belong to this group"}
            )
        
        if request.accumulator_id is not None:
            group_accumulator.accumulator_id = request.accumulator_id
        if request.title is not None:
            group_accumulator.title = request.title
        if request.target_count is not None:
            group_accumulator.target_count = request.target_count
        if request.start_date is not None:
            group_accumulator.start_date = request.start_date
        if request.end_date is not None:
            group_accumulator.end_date = request.end_date
        
        updated = update_group_accumulator(db, group_accumulator)
        return _convert_to_dto(updated)


def delete_group_accumulator_cms_service(
    token: str,
    group_id: UUID,
    group_accumulator_id: UUID,
) -> None:
    """Delete a group accumulator (CMS - requires author with status change permission)."""
    author = validate_cms_author_details(token=token)
    with SessionLocal() as db:
        require_can_change_status(db=db, group_id=group_id, author=author)
        
        group_accumulator = get_group_accumulator_by_id(db, group_accumulator_id)
        if not group_accumulator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NOT_FOUND", "message": "Group accumulator not found"}
            )
        
        if group_accumulator.group_id != group_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "FORBIDDEN", "message": "Group accumulator does not belong to this group"}
            )
        
        delete_group_accumulator(db, group_accumulator)
