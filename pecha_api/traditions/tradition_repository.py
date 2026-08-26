from typing import List, Optional, Sequence
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from starlette import status

from pecha_api.plans.plans_enums import LanguageCode
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import NOT_FOUND
from pecha_api.traditions.tradition_constants import (
    parse_language_code,
    tradition_id_from_code,
)
from pecha_api.traditions.tradition_models import Tradition, TraditionMetadata, UserTradition
from pecha_api.traditions.tradition_response_models import TraditionMetadataInput


def get_user_traditions(db: Session, user_id: UUID) -> List[UserTradition]:
    return (
        db.query(UserTradition)
        .options(joinedload(UserTradition.tradition).joinedload(Tradition.metadata_entries))
        .filter(UserTradition.user_id == user_id)
        .order_by(UserTradition.created_at.desc())
        .all()
    )


def _managed_traditions_query(db: Session):
    return (
        db.query(Tradition)
        .options(joinedload(Tradition.metadata_entries))
        .filter(~Tradition.code.like("legacy_%"))
    )


def list_traditions(db: Session) -> List[Tradition]:
    return _managed_traditions_query(db).order_by(Tradition.code.asc()).all()


def list_traditions_cms(
    db: Session,
    *,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[List[Tradition], int]:
    filters = [~Tradition.code.like("legacy_%")]
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(
                Tradition.code.ilike(pattern),
                Tradition.metadata_entries.any(TraditionMetadata.name.ilike(pattern)),
            )
        )

    total = (
        db.query(func.count(Tradition.id))
        .filter(*filters)
        .scalar()
        or 0
    )
    traditions = (
        db.query(Tradition)
        .options(joinedload(Tradition.metadata_entries))
        .filter(*filters)
        .order_by(Tradition.code.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return traditions, int(total)


def get_tradition_by_id(db: Session, tradition_id: UUID) -> Optional[Tradition]:
    return (
        db.query(Tradition)
        .options(joinedload(Tradition.metadata_entries))
        .filter(Tradition.id == tradition_id)
        .first()
    )


def get_tradition_by_code(db: Session, tradition_code: str) -> Optional[Tradition]:
    return (
        db.query(Tradition)
        .options(joinedload(Tradition.metadata_entries))
        .filter(Tradition.code == tradition_code)
        .first()
    )


def resolve_tradition_metadata(
    tradition: Tradition,
    language: str | LanguageCode,
) -> Optional[TraditionMetadata]:
    if not tradition.metadata_entries:
        return None

    language_code = (
        language
        if isinstance(language, LanguageCode)
        else parse_language_code(language)
    )
    by_language = {entry.language: entry for entry in tradition.metadata_entries}
    return by_language.get(language_code) or by_language.get(LanguageCode.EN)


def _parse_metadata_language(language: str) -> LanguageCode:
    try:
        return LanguageCode(language.strip().upper())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language code: {language}",
        ) from exc


def _upsert_metadata_entries(
    db: Session,
    tradition: Tradition,
    metadata_inputs: Sequence[TraditionMetadataInput],
) -> None:
    existing_by_language = {
        entry.language: entry for entry in (tradition.metadata_entries or [])
    }
    for meta_input in metadata_inputs:
        language = _parse_metadata_language(meta_input.language)
        existing = existing_by_language.get(language)
        other_names = meta_input.other_names
        if existing is None:
            entry = TraditionMetadata(
                id=uuid4(),
                tradition_id=tradition.id,
                language=language,
                name=meta_input.name.strip(),
                description=(meta_input.description or None),
                other_names=other_names,
            )
            db.add(entry)
            existing_by_language[language] = entry
        else:
            existing.name = meta_input.name.strip()
            existing.description = meta_input.description or None
            existing.other_names = other_names


def create_tradition(
    db: Session,
    *,
    code: str,
    regions: Optional[List[str]],
    parent_id: Optional[UUID],
    metadata_inputs: Sequence[TraditionMetadataInput],
) -> Tradition:
    existing = get_tradition_by_code(db=db, tradition_code=code)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ResponseError(
                error="CONFLICT",
                message=f"Tradition with code '{code}' already exists",
            ).model_dump(),
        )

    if parent_id is not None and get_tradition_by_id(db=db, tradition_id=parent_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parent tradition '{parent_id}' not found",
        )

    tradition = Tradition(
        id=tradition_id_from_code(code),
        code=code,
        parent_id=parent_id,
        regions=regions or [],
    )
    db.add(tradition)
    db.flush()
    tradition.metadata_entries = []
    _upsert_metadata_entries(db=db, tradition=tradition, metadata_inputs=metadata_inputs)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ResponseError(
                error="CONFLICT",
                message=f"Tradition with code '{code}' already exists",
            ).model_dump(),
        ) from exc

    created = get_tradition_by_id(db=db, tradition_id=tradition.id)
    if created is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load created tradition",
        )
    return created


def update_tradition(
    db: Session,
    *,
    tradition_id: UUID,
    code: Optional[str],
    regions: Optional[List[str]],
    parent_id: Optional[UUID],
    metadata_inputs: Optional[Sequence[TraditionMetadataInput]],
) -> Tradition:
    tradition = get_tradition_by_id(db=db, tradition_id=tradition_id)
    if tradition is None or tradition.code.startswith("legacy_"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ResponseError(
                error=NOT_FOUND,
                message=f"Tradition with ID {tradition_id} not found",
            ).model_dump(),
        )

    if code is not None and code != tradition.code:
        conflict = get_tradition_by_code(db=db, tradition_code=code)
        if conflict is not None and conflict.id != tradition.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ResponseError(
                    error="CONFLICT",
                    message=f"Tradition with code '{code}' already exists",
                ).model_dump(),
            )
        tradition.code = code

    if regions is not None:
        tradition.regions = regions

    if parent_id is not None:
        if parent_id == tradition.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A tradition cannot be its own parent",
            )
        if get_tradition_by_id(db=db, tradition_id=parent_id) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent tradition '{parent_id}' not found",
            )
        tradition.parent_id = parent_id

    if metadata_inputs is not None:
        if len(metadata_inputs) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one metadata language is required",
            )
        _upsert_metadata_entries(db=db, tradition=tradition, metadata_inputs=metadata_inputs)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ResponseError(
                error="CONFLICT",
                message="Tradition update conflict",
            ).model_dump(),
        ) from exc

    updated = get_tradition_by_id(db=db, tradition_id=tradition.id)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load updated tradition",
        )
    return updated


def delete_tradition(db: Session, tradition_id: UUID) -> None:
    tradition = get_tradition_by_id(db=db, tradition_id=tradition_id)
    if tradition is None or tradition.code.startswith("legacy_"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ResponseError(
                error=NOT_FOUND,
                message=f"Tradition with ID {tradition_id} not found",
            ).model_dump(),
        )
    db.delete(tradition)
    db.commit()


def save_user_tradition(db: Session, user_id: UUID, tradition_code: str) -> UserTradition:
    tradition = get_tradition_by_code(db=db, tradition_code=tradition_code)
    if tradition is None or tradition.code.startswith("legacy_"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ResponseError(
                error=NOT_FOUND,
                message=f"Tradition '{tradition_code}' is not available",
            ).model_dump(),
        )

    existing = (
        db.query(UserTradition)
        .filter(
            UserTradition.user_id == user_id,
            UserTradition.tradition_id == tradition.id,
        )
        .first()
    )
    if existing is not None:
        if existing.tradition is None:
            existing.tradition = tradition
        return existing

    user_tradition = UserTradition(
        user_id=user_id,
        tradition_id=tradition.id,
    )
    try:
        db.add(user_tradition)
        db.commit()
        db.refresh(user_tradition)
        user_tradition.tradition = tradition
        return user_tradition
    except IntegrityError:
        db.rollback()
        existing = (
            db.query(UserTradition)
            .options(joinedload(UserTradition.tradition).joinedload(Tradition.metadata_entries))
            .filter(
                UserTradition.user_id == user_id,
                UserTradition.tradition_id == tradition.id,
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
    user_tradition = (
        db.query(UserTradition)
        .options(joinedload(UserTradition.tradition).joinedload(Tradition.metadata_entries))
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

    tradition = get_tradition_by_code(db=db, tradition_code=tradition_code)
    if tradition is None or tradition.code.startswith("legacy_"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ResponseError(
                error=NOT_FOUND,
                message=f"Tradition '{tradition_code}' is not available",
            ).model_dump(),
        )

    if user_tradition.tradition_id == tradition.id:
        user_tradition.tradition = tradition
        return user_tradition

    conflicting = (
        db.query(UserTradition)
        .filter(
            UserTradition.user_id == user_id,
            UserTradition.tradition_id == tradition.id,
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

    user_tradition.tradition_id = tradition.id
    db.commit()
    db.refresh(user_tradition)
    user_tradition.tradition = tradition
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
