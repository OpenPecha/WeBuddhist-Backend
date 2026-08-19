from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.error_contants import ErrorConstants
from pecha_api.push_devices.push_device_enums import PushPlatform
from pecha_api.push_devices.push_device_models import PushDeviceToken
from pecha_api.push_devices.push_device_repository import (
    count_push_device_tokens,
    delete_push_device_token,
    delete_push_device_token_by_token,
    get_active_push_device_tokens_by_user_id,
    get_all_push_device_tokens,
    get_push_device_token_by_token,
    get_push_device_token_by_user_and_device_id,
    save_push_device_token,
)
from pecha_api.push_devices.push_device_response_models import (
    AdminPushDeviceTokenDTO,
    AdminPushDeviceTokensListResponse,
    PushDeviceTokenDTO,
    PushDeviceTokensResponse,
    RegisterPushDeviceRequest,
)
from pecha_api.users.users_service import validate_and_extract_user_details, verify_admin_access


def _to_dto(push_device_token: PushDeviceToken) -> PushDeviceTokenDTO:
    return PushDeviceTokenDTO(
        id=push_device_token.id,
        platform=push_device_token.platform,
        device_id=push_device_token.device_id,
        is_active=push_device_token.is_active,
        created_at=push_device_token.created_at,
        updated_at=push_device_token.updated_at,
    )


def _upsert_push_device_token(
    db: Session,
    user_id: UUID,
    token: str,
    platform: PushPlatform,
    device_id: Optional[str] = None,
) -> PushDeviceToken:
    now = datetime.now(timezone.utc)

    if device_id is not None:
        existing_installation = get_push_device_token_by_user_and_device_id(
            db=db,
            user_id=user_id,
            device_id=device_id,
        )
        if existing_installation is not None:
            if existing_installation.token == token:
                existing_installation.is_active = True
                existing_installation.updated_at = now
                return save_push_device_token(db=db, push_device_token=existing_installation)

            delete_push_device_token_by_token(
                db=db,
                token=token,
                exclude_id=existing_installation.id,
            )
            existing_installation.token = token
            existing_installation.platform = platform
            existing_installation.is_active = True
            existing_installation.updated_at = now
            return save_push_device_token(db=db, push_device_token=existing_installation)

    existing_by_token = get_push_device_token_by_token(db=db, token=token)
    if existing_by_token is not None and existing_by_token.user_id == user_id:
        existing_by_token.platform = platform
        if device_id is not None:
            existing_by_token.device_id = device_id
        existing_by_token.is_active = True
        existing_by_token.updated_at = now
        return save_push_device_token(db=db, push_device_token=existing_by_token)

    delete_push_device_token_by_token(db=db, token=token)

    push_device_token = PushDeviceToken(
        user_id=user_id,
        token=token,
        platform=platform,
        device_id=device_id,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    return save_push_device_token(db=db, push_device_token=push_device_token, is_new=True)


async def register_push_device_service(
    token: str,
    register_request: RegisterPushDeviceRequest,
) -> PushDeviceTokenDTO:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        push_device_token = _upsert_push_device_token(
            db=db,
            user_id=current_user.id,
            token=register_request.token,
            platform=register_request.platform,
            device_id=register_request.device_id,
        )
        return _to_dto(push_device_token)


async def get_push_devices_service(token: str) -> PushDeviceTokensResponse:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        push_device_tokens = get_active_push_device_tokens_by_user_id(
            db=db,
            user_id=current_user.id,
        )
        return PushDeviceTokensResponse(
            devices=[_to_dto(push_device_token) for push_device_token in push_device_tokens],
        )


async def delete_push_device_service(token: str, push_device_token_id: UUID) -> None:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        delete_push_device_token(
            db=db,
            user_id=current_user.id,
            push_device_token_id=push_device_token_id,
        )


def _to_admin_dto(push_device_token: PushDeviceToken) -> AdminPushDeviceTokenDTO:
    return AdminPushDeviceTokenDTO(
        id=push_device_token.id,
        user_id=push_device_token.user_id,
        token=push_device_token.token,
        platform=push_device_token.platform,
        device_id=push_device_token.device_id,
        is_active=push_device_token.is_active,
        created_at=push_device_token.created_at,
        updated_at=push_device_token.updated_at,
    )


async def list_all_push_devices_service(
    token: str,
    skip: int = 0,
    limit: int = 100,
    platform: Optional[PushPlatform] = None,
    active_only: bool = True,
) -> AdminPushDeviceTokensListResponse:
    if not verify_admin_access(token=token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorConstants.ADMIN_ERROR_MESSAGE,
        )

    with SessionLocal() as db:
        push_device_tokens = get_all_push_device_tokens(
            db=db,
            skip=skip,
            limit=limit,
            platform=platform,
            active_only=active_only,
        )
        total = count_push_device_tokens(
            db=db,
            platform=platform,
            active_only=active_only,
        )

        return AdminPushDeviceTokensListResponse(
            devices=[_to_admin_dto(push_device_token) for push_device_token in push_device_tokens],
            total=total,
            skip=skip,
            limit=limit,
        )
