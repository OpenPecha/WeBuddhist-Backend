from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from starlette import status

from pecha_api.plans.plans_enums import LanguageCode
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import NOT_FOUND
from pecha_api.traditions.tradition_constants import tradition_id_from_code
from pecha_api.traditions.tradition_models import Tradition, TraditionMetadata, UserTradition
from pecha_api.traditions.tradition_onboarding import (
    get_tradition_path_entry,
    list_tradition_path_codes,
)


def get_user_traditions(db: Session, user_id: UUID) -> List[UserTradition]:
    return (
        db.query(UserTradition)
        .options(joinedload(UserTradition.tradition).joinedload(Tradition.metadata_entries))
        .filter(UserTradition.user_id == user_id)
        .order_by(UserTradition.created_at.desc())
        .all()
    )


def ensure_path_tradition_exists(db: Session, tradition_code: str) -> UUID:
    tradition_id = tradition_id_from_code(tradition_code)
    existing = db.query(Tradition).filter(Tradition.id == tradition_id).first()
    if existing is not None:
        return tradition_id

    path_entry = get_tradition_path_entry(tradition_code)
    if path_entry is None:
        raise ValueError(f"Unknown tradition code: {tradition_code}")

    tradition = Tradition(
        id=tradition_id,
        parent_id=None,
        regions=None,
    )
    db.add(tradition)
    metadata = TraditionMetadata(
        tradition_id=tradition_id,
        language=LanguageCode.EN,
        name=path_entry["title"],
        other_names=None,
    )
    db.add(metadata)
    db.commit()
    return tradition_id


def save_user_tradition(db: Session, user_id: UUID, tradition_code: str) -> UserTradition:
    if tradition_code not in list_tradition_path_codes():
        raise ValueError(f"Unknown tradition code: {tradition_code}")

    tradition_id = ensure_path_tradition_exists(db=db, tradition_code=tradition_code)

    existing = (
        db.query(UserTradition)
        .filter(
            UserTradition.user_id == user_id,
            UserTradition.tradition_id == tradition_id,
        )
        .first()
    )
    if existing is not None:
        return existing

    user_tradition = UserTradition(
        user_id=user_id,
        tradition_id=tradition_id,
    )
    try:
        db.add(user_tradition)
        db.commit()
        db.refresh(user_tradition)
        return user_tradition
    except IntegrityError:
        db.rollback()
        existing = (
            db.query(UserTradition)
            .filter(
                UserTradition.user_id == user_id,
                UserTradition.tradition_id == tradition_id,
            )
            .first()
        )
        if existing is None:
            raise
        return existing


def update_user_tradition(
    db: Session,
    user_id: UUID,
    user_tradition_id: UUID,
    tradition_code: str,
) -> UserTradition:
    if tradition_code not in list_tradition_path_codes():
        raise ValueError(f"Unknown tradition code: {tradition_code}")

    user_tradition = (
        db.query(UserTradition)
        .filter(
            UserTradition.id == user_tradition_id,
            UserTradition.user_id == user_id,
        )
        .first()
    )
    if user_tradition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ResponseError(
                error=NOT_FOUND,
                message=f"User tradition with ID {user_tradition_id} not found",
            ).model_dump(),
        )

    tradition_id = ensure_path_tradition_exists(db=db, tradition_code=tradition_code)
    if user_tradition.tradition_id == tradition_id:
        return user_tradition

    conflicting = (
        db.query(UserTradition)
        .filter(
            UserTradition.user_id == user_id,
            UserTradition.tradition_id == tradition_id,
            UserTradition.id != user_tradition_id,
        )
        .first()
    )
    if conflicting is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ResponseError(
                error="CONFLICT",
                message="User already has this tradition",
            ).model_dump(),
        )

    user_tradition.tradition_id = tradition_id
    db.commit()
    db.refresh(user_tradition)
    return user_tradition


def delete_user_tradition(db: Session, user_id: UUID, user_tradition_id: UUID) -> None:
    user_tradition = (
        db.query(UserTradition)
        .filter(
            UserTradition.id == user_tradition_id,
            UserTradition.user_id == user_id,
        )
        .first()
    )
    if user_tradition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ResponseError(
                error=NOT_FOUND,
                message=f"User tradition with ID {user_tradition_id} not found",
            ).model_dump(),
        )

    db.delete(user_tradition)
    db.commit()
