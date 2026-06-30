from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from starlette import status

from pecha_api.plans.plans_enums import LanguageCode
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import NOT_FOUND
from pecha_api.traditions.tradition_models import Tradition, TraditionMetadata, UserTradition
from pecha_api.traditions.tradition_taxonomy import (
    get_tradition_entry,
    load_tradition_taxonomy,
    tradition_id_from_code,
)


def get_tradition_by_code(db: Session, code: str) -> Optional[Tradition]:
    tradition_id = tradition_id_from_code(code)
    return db.query(Tradition).filter(Tradition.id == tradition_id).first()


def sync_traditions_from_taxonomy(db: Session) -> None:
    taxonomy = load_tradition_taxonomy()
    code_to_uuid = {
        entry["id"]: tradition_id_from_code(entry["id"])
        for entry in taxonomy["traditions"]
    }

    for entry in taxonomy["traditions"]:
        tradition_id = code_to_uuid[entry["id"]]
        parent_code = entry.get("parent")
        parent_id = code_to_uuid.get(parent_code) if parent_code else None

        tradition = db.query(Tradition).filter(Tradition.id == tradition_id).first()
        if tradition is None:
            tradition = Tradition(
                id=tradition_id,
                parent_id=parent_id,
                regions=entry.get("regions"),
            )
            db.add(tradition)
        else:
            tradition.parent_id = parent_id
            tradition.regions = entry.get("regions")

        for language_code, localized_names in entry.get("names", {}).items():
            language = LanguageCode[language_code.upper()]
            metadata = (
                db.query(TraditionMetadata)
                .filter(
                    TraditionMetadata.tradition_id == tradition_id,
                    TraditionMetadata.language == language,
                )
                .first()
            )
            if metadata is None:
                metadata = TraditionMetadata(
                    tradition_id=tradition_id,
                    language=language,
                    name=localized_names.get("name", entry["id"]),
                    other_names=localized_names.get("aliases"),
                )
                db.add(metadata)
            else:
                metadata.name = localized_names.get("name", entry["id"])
                metadata.other_names = localized_names.get("aliases")

    db.commit()


def get_user_traditions(db: Session, user_id: UUID) -> List[UserTradition]:
    return (
        db.query(UserTradition)
        .options(joinedload(UserTradition.tradition).joinedload(Tradition.metadata_entries))
        .filter(UserTradition.user_id == user_id)
        .order_by(UserTradition.created_at.desc())
        .all()
    )


def ensure_tradition_exists(db: Session, tradition_code: str) -> UUID:
    tradition_id = tradition_id_from_code(tradition_code)
    existing = db.query(Tradition).filter(Tradition.id == tradition_id).first()
    if existing is None:
        sync_traditions_from_taxonomy(db)
    return tradition_id


def ensure_custom_tradition_exists(db: Session, tradition_label: str) -> UUID:
    tradition_id = tradition_id_from_code(tradition_label)
    existing = db.query(Tradition).filter(Tradition.id == tradition_id).first()
    if existing is not None:
        return tradition_id

    tradition = Tradition(
        id=tradition_id,
        parent_id=None,
        regions=None,
    )
    db.add(tradition)
    metadata = TraditionMetadata(
        tradition_id=tradition_id,
        language=LanguageCode.EN,
        name=tradition_label,
        other_names=None,
    )
    db.add(metadata)
    db.commit()
    return tradition_id


def save_user_tradition(db: Session, user_id: UUID, tradition_code: str) -> UserTradition:
    if get_tradition_entry(tradition_code) is not None:
        tradition_id = ensure_tradition_exists(db=db, tradition_code=tradition_code)
    else:
        tradition_id = ensure_custom_tradition_exists(db=db, tradition_label=tradition_code)

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
