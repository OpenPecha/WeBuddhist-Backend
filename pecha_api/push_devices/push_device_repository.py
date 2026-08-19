from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette import status

from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import NOT_FOUND
from pecha_api.push_devices.push_device_enums import PushPlatform
from pecha_api.push_devices.push_device_models import PushDeviceToken


def get_push_device_token_by_token(db: Session, token: str) -> Optional[PushDeviceToken]:
    return db.query(PushDeviceToken).filter(PushDeviceToken.token == token).first()


def get_push_device_token_by_user_and_device_id(
    db: Session,
    user_id: UUID,
    device_id: str,
) -> Optional[PushDeviceToken]:
    return (
        db.query(PushDeviceToken)
        .filter(
            PushDeviceToken.user_id == user_id,
            PushDeviceToken.device_id == device_id,
        )
        .first()
    )


def get_all_push_device_tokens(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    platform: Optional[PushPlatform] = None,
    active_only: bool = True,
) -> List[PushDeviceToken]:
    query = db.query(PushDeviceToken)

    if active_only:
        query = query.filter(PushDeviceToken.is_active.is_(True))

    if platform is not None:
        query = query.filter(PushDeviceToken.platform == platform)

    return (
        query.order_by(PushDeviceToken.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_push_device_tokens(
    db: Session,
    platform: Optional[PushPlatform] = None,
    active_only: bool = True,
) -> int:
    query = db.query(PushDeviceToken)

    if active_only:
        query = query.filter(PushDeviceToken.is_active.is_(True))

    if platform is not None:
        query = query.filter(PushDeviceToken.platform == platform)

    return query.count()


def get_active_push_device_tokens_by_user_id(db: Session, user_id: UUID) -> List[PushDeviceToken]:
    return (
        db.query(PushDeviceToken)
        .filter(
            PushDeviceToken.user_id == user_id,
            PushDeviceToken.is_active.is_(True),
        )
        .order_by(PushDeviceToken.updated_at.desc())
        .all()
    )


def delete_push_device_token_by_token(
    db: Session,
    token: str,
    exclude_id: Optional[UUID] = None,
) -> None:
    query = db.query(PushDeviceToken).filter(PushDeviceToken.token == token)
    if exclude_id is not None:
        query = query.filter(PushDeviceToken.id != exclude_id)

    conflicting_records = query.all()
    if not conflicting_records:
        return

    for conflicting in conflicting_records:
        db.delete(conflicting)
    db.flush()


def save_push_device_token(
    db: Session,
    push_device_token: PushDeviceToken,
    is_new: bool = False,
) -> PushDeviceToken:
    return _commit_push_device_token(
        db=db,
        push_device_token=push_device_token,
        is_new=is_new,
    )


def delete_push_device_token(db: Session, user_id: UUID, push_device_token_id: UUID) -> None:
    push_device_token = (
        db.query(PushDeviceToken)
        .filter(
            PushDeviceToken.id == push_device_token_id,
            PushDeviceToken.user_id == user_id,
        )
        .first()
    )

    if not push_device_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ResponseError(
                error=NOT_FOUND,
                message=f"Push device token with ID {push_device_token_id} not found for this user",
            ).model_dump(),
        )

    db.delete(push_device_token)
    db.commit()


def _commit_push_device_token(
    db: Session,
    push_device_token: PushDeviceToken,
    is_new: bool = False,
) -> PushDeviceToken:
    try:
        if is_new:
            db.add(push_device_token)
        db.commit()
        db.refresh(push_device_token)
        return push_device_token
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ResponseError(
                error="CONFLICT",
                message=f"Push device token conflict: {error.orig}",
            ).model_dump(),
        ) from error
