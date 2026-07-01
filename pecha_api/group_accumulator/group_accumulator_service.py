from typing import List, Optional, Tuple
from uuid import UUID
from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.users.users_service import validate_and_extract_user_details
from pecha_api.timezone_utils import get_day_bounds_in_timezone, normalize_timezone_name
from pecha_api.plans.authors.plan_authors_service import validate_cms_author_details
from pecha_api.plans.shared.permissions import (
    require_can_create_content,
    require_can_read_group_content,
    require_can_change_status,
)
from pecha_api.config import get
from pecha_api.plans.authors.plan_authors_service import get_image_url
from pecha_api.plans.groups.groups_enums import AuthorGroupType
from pecha_api.plans.groups.groups_repository import (
    get_group_by_id,
    is_user_joined_group,
    upsert_group_join,
)
from pecha_api.uploads.S3_utils import generate_presigned_access_url
from pecha_api.users.users_models import Users
from .group_accumulator_repository import (
    create_group_accumulator,
    get_group_accumulators,
    get_group_accumulator_by_id,
    update_group_accumulator,
    delete_group_accumulator,
    add_group_history_row,
    get_group_accumulator_history,
    get_group_accumulator_total_count,
    get_group_accumulator_count_in_range,
    get_user_group_accumulator_count,
    verify_group_exists,
    upsert_group_accumulator_join,
    is_user_joined_group_accumulator,
    get_group_accumulator_joiners_count,
    list_group_accumulator_joiners_paginated,
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
    GroupAccumulatorMemberDTO,
    GroupAccumulatorMembersResponse,
)


def _to_group_type(value) -> AuthorGroupType:
    if hasattr(value, "value"):
        return AuthorGroupType(value.value)
    return AuthorGroupType(value)


def _assert_group_allows_join(group) -> None:
    if _to_group_type(group.group_type) != AuthorGroupType.COMMUNITY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "This group does not support joining"},
        )


def _user_fullname(user: Users) -> str:
    parts = [user.firstname, user.lastname]
    return " ".join(part for part in parts if part).strip()


def _user_avatar_url(user: Users) -> str | None:
    if not user.avatar_url:
        return None
    return generate_presigned_access_url(
        bucket_name=get("AWS_BUCKET_NAME"),
        s3_key=user.avatar_url,
    )


def _convert_to_dto(group_accumulator) -> GroupAccumulatorDTO:
    return GroupAccumulatorDTO(
        id=group_accumulator.id,
        accumulator_id=group_accumulator.accumulator_id,
        group_id=group_accumulator.group_id,
        title=group_accumulator.title,
        image=get_image_url(group_accumulator.image_key),
        image_key=group_accumulator.image_key,
        target_count=group_accumulator.target_count,
        start_date=group_accumulator.start_date,
        end_date=group_accumulator.end_date,
        created_at=group_accumulator.created_at,
        updated_at=group_accumulator.updated_at,
    )


def _today_bounds(timezone_name: Optional[str]) -> Tuple:
    normalized = normalize_timezone_name(timezone_name)
    return get_day_bounds_in_timezone(normalized)


def _convert_to_detail_dto(
    group_accumulator,
    *,
    total_count: int,
    total_today_count: int,
    member_count: int,
    user_total_count: Optional[int] = None,
    user_today_count: Optional[int] = None,
) -> GroupAccumulatorDetailDTO:
    return GroupAccumulatorDetailDTO(
        id=group_accumulator.id,
        accumulator_id=group_accumulator.accumulator_id,
        group_id=group_accumulator.group_id,
        title=group_accumulator.title,
        image=get_image_url(group_accumulator.image_key),
        image_key=group_accumulator.image_key,
        target_count=group_accumulator.target_count,
        start_date=group_accumulator.start_date,
        end_date=group_accumulator.end_date,
        total_count=total_count,
        total_today_count=total_today_count,
        user_total_count=user_total_count,
        user_today_count=user_today_count,
        member_count=member_count,
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
            image_key=request.image_key,
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
    timezone_name: Optional[str] = None,
    token: Optional[str] = None,
) -> GroupAccumulatorDetailDTO:
    with SessionLocal() as db:
        group_accumulator = get_group_accumulator_by_id(db, group_accumulator_id)
        if not group_accumulator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NOT_FOUND", "message": "Group accumulator not found"}
            )
        
        total_count = get_group_accumulator_total_count(db, group_accumulator_id)
        member_count = get_group_accumulator_joiners_count(db, group_accumulator_id)
        day_start, day_end = _today_bounds(timezone_name)
        total_today_count = get_group_accumulator_count_in_range(
            db=db,
            group_accumulator_id=group_accumulator_id,
            range_start=day_start,
            range_end=day_end,
        )

        user_total_count = None
        user_today_count = None
        if token:
            current_user = validate_and_extract_user_details(token=token)
            user_total_count = get_user_group_accumulator_count(
                db=db,
                group_accumulator_id=group_accumulator_id,
                user_id=current_user.id,
            )
            user_today_count = get_group_accumulator_count_in_range(
                db=db,
                group_accumulator_id=group_accumulator_id,
                range_start=day_start,
                range_end=day_end,
                user_id=current_user.id,
            )

        return _convert_to_detail_dto(
            group_accumulator,
            total_count=total_count,
            total_today_count=total_today_count,
            member_count=member_count,
            user_total_count=user_total_count,
            user_today_count=user_today_count,
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
        if request.image_key is not None:
            group_accumulator.image_key = request.image_key
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


def join_group_accumulator_service(
    token: str,
    group_accumulator_id: UUID,
) -> None:
    """Join a group accumulator and automatically join the parent group."""
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        group_accumulator = get_group_accumulator_by_id(db, group_accumulator_id)
        if not group_accumulator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NOT_FOUND", "message": "Group accumulator not found"},
            )

        group = get_group_by_id(db=db, group_id=group_accumulator.group_id)
        if not group or not group.is_public:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NOT_FOUND", "message": "Group not found"},
            )

        _assert_group_allows_join(group)
        upsert_group_join(db=db, group_id=group_accumulator.group_id, user_id=current_user.id)
        upsert_group_accumulator_join(
            db=db,
            group_accumulator_id=group_accumulator_id,
            user_id=current_user.id,
        )


def get_group_accumulator_members_service(
    group_accumulator_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> GroupAccumulatorMembersResponse:
    with SessionLocal() as db:
        group_accumulator = get_group_accumulator_by_id(db, group_accumulator_id)
        if not group_accumulator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NOT_FOUND", "message": "Group accumulator not found"},
            )

        rows, total = list_group_accumulator_joiners_paginated(
            db=db,
            group_accumulator_id=group_accumulator_id,
            skip=skip,
            limit=limit,
        )

        return GroupAccumulatorMembersResponse(
            members=[
                GroupAccumulatorMemberDTO(
                    user_id=user.id,
                    username=user.username,
                    fullname=_user_fullname(user),
                    avatar_url=_user_avatar_url(user),
                    joined_at=joined_at,
                )
                for user, joined_at in rows
            ],
            total=total,
            skip=skip,
            limit=limit,
        )


def delete_group_accumulator_user_service(
    token: str,
    group_accumulator_id: UUID,
) -> None:
    """Delete a group accumulator (User - requires group membership)."""
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
        
        # Verify user has joined this group accumulator
        if not is_user_joined_group_accumulator(
            db=db,
            group_accumulator_id=group_accumulator_id,
            user_id=current_user.id,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "FORBIDDEN", "message": "You must join this group accumulator first"},
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
    today_only: bool = False,
    timezone_name: Optional[str] = None,
) -> GroupAccumulatorHistoryResponse:
    with SessionLocal() as db:
        group_accumulator = get_group_accumulator_by_id(db, group_accumulator_id)
        if not group_accumulator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NOT_FOUND", "message": "Group accumulator not found"}
            )

        day_start, day_end = _today_bounds(timezone_name)
        range_start = day_start if today_only else None
        range_end = day_end if today_only else None

        history, total = get_group_accumulator_history(
            db,
            group_accumulator_id,
            skip,
            limit,
            range_start=range_start,
            range_end=range_end,
        )
        total_count = get_group_accumulator_total_count(db, group_accumulator_id)
        total_today_count = get_group_accumulator_count_in_range(
            db=db,
            group_accumulator_id=group_accumulator_id,
            range_start=day_start,
            range_end=day_end,
        )
        member_count = get_group_accumulator_joiners_count(db, group_accumulator_id)

        return GroupAccumulatorHistoryResponse(
            group_accumulator=_convert_to_detail_dto(
                group_accumulator,
                total_count=total_count,
                total_today_count=total_today_count,
                member_count=member_count,
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
            image_key=request.image_key,
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
        member_count = get_group_accumulator_joiners_count(db, group_accumulator_id)
        day_start, day_end = _today_bounds(timezone_name=None)
        total_today_count = get_group_accumulator_count_in_range(
            db=db,
            group_accumulator_id=group_accumulator_id,
            range_start=day_start,
            range_end=day_end,
        )

        return _convert_to_detail_dto(
            group_accumulator,
            total_count=total_count,
            total_today_count=total_today_count,
            member_count=member_count,
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
        if request.image_key is not None:
            group_accumulator.image_key = request.image_key
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
