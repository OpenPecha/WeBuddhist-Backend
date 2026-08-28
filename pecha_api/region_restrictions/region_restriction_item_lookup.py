"""Resolve display titles and search candidates for China-restricted items."""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session, selectinload

from pecha_api.accumulator.accumulator_enums import AccumulatorType
from pecha_api.accumulator.accumulator_metadata_model import AccumulatorMetadata
from pecha_api.accumulator.accumulator_models import Accumulator
from pecha_api.accumulator.group_accumulator_models import GroupAccumulator
from pecha_api.mantra.mantra_metadata_model import MantraMetadata
from pecha_api.mantra.mantra_model import Mantra
from pecha_api.mantra.mantra_repository import get_mantras_by_ids
from pecha_api.plans.groups.groups_models import AuthorGroup, AuthorGroupMetadata
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.series.series_metadata_model import SeriesMetadata
from pecha_api.plans.series.series_model import Series
from pecha_api.plans.users.recitation_collection.recitation_collection_models import (
    RecitationCollection,
)
from pecha_api.region_restrictions.region_restriction_enums import RestrictedItemType
from pecha_api.region_restrictions.region_restriction_response_models import (
    ChinaRestrictionCandidateDTO,
)


def _lang_value(language) -> str:
    if language is None:
        return ""
    return language.value if hasattr(language, "value") else str(language)


def _pick_metadata_text(
    entries: Sequence,
    *,
    field: str = "title",
) -> Optional[str]:
    if not entries:
        return None
    preferred = ("EN", "BO", "ZH")
    by_lang = {
        _lang_value(getattr(entry, "language", None)).upper(): entry
        for entry in entries
    }
    for code in preferred:
        entry = by_lang.get(code)
        if entry is None:
            continue
        value = getattr(entry, field, None)
        if value and str(value).strip():
            return str(value).strip()
    for entry in entries:
        value = getattr(entry, field, None)
        if value and str(value).strip():
            return str(value).strip()
    return None


def _mantra_display_title(mantra: Mantra) -> Optional[str]:
    title = _pick_metadata_text(mantra.metadata_entries or [], field="title")
    if title:
        return title
    mantra_text = _pick_metadata_text(mantra.metadata_entries or [], field="mantra")
    if mantra_text:
        return mantra_text if len(mantra_text) <= 80 else f"{mantra_text[:77]}…"
    return None


def _accumulator_display_title(
    accumulator: Accumulator,
    mantras_by_id: Optional[Dict[UUID, Mantra]] = None,
) -> Optional[str]:
    name = _pick_metadata_text(accumulator.metadata_entries or [], field="name")
    if name:
        return name
    if mantras_by_id and accumulator.mantra_id:
        mantra = mantras_by_id.get(accumulator.mantra_id)
        if mantra is not None:
            return _mantra_display_title(mantra)
    return None


def resolve_titles_for_rows(
    db: Session,
    *,
    item_type: RestrictedItemType,
    item_ids: Sequence[str],
) -> Dict[str, str]:
    # item_id is a plain string column now (it also holds non-UUID OpenPecha
    # text ids for RECITATION), so every branch below keys its result by
    # str(id) to match, even though the underlying entities still use native
    # UUID primary keys.
    ids = list({item_id for item_id in item_ids if item_id is not None})
    if not ids:
        return {}

    if item_type == RestrictedItemType.PLAN:
        rows = (
            db.query(Plan.id, Plan.title)
            .filter(Plan.id.in_(ids), Plan.deleted_at.is_(None))
            .all()
        )
        return {str(row.id): row.title for row in rows if row.title}

    if item_type == RestrictedItemType.SERIES:
        series_rows = (
            db.query(Series)
            .options(selectinload(Series.metadata_entries))
            .filter(Series.id.in_(ids), Series.deleted_at.is_(None))
            .all()
        )
        return {
            str(series.id): title
            for series in series_rows
            if (title := _pick_metadata_text(series.metadata_entries or []))
        }

    if item_type == RestrictedItemType.GROUP:
        groups = (
            db.query(AuthorGroup)
            .options(selectinload(AuthorGroup.metadata_entries))
            .filter(AuthorGroup.id.in_(ids), AuthorGroup.deleted_at.is_(None))
            .all()
        )
        return {
            str(group.id): title
            for group in groups
            if (title := _pick_metadata_text(group.metadata_entries or []))
        }

    if item_type == RestrictedItemType.MANTRA:
        mantras = (
            db.query(Mantra)
            .options(selectinload(Mantra.metadata_entries))
            .filter(Mantra.id.in_(ids))
            .all()
        )
        return {
            str(mantra.id): title
            for mantra in mantras
            if (title := _mantra_display_title(mantra))
        }

    if item_type == RestrictedItemType.ACCUMULATOR:
        accumulators = (
            db.query(Accumulator)
            .options(selectinload(Accumulator.metadata_entries))
            .filter(Accumulator.id.in_(ids), Accumulator.deleted_at.is_(None))
            .all()
        )
        mantra_ids = [
            acc.mantra_id for acc in accumulators if acc.mantra_id is not None
        ]
        mantras_by_id = get_mantras_by_ids(db, mantra_ids)
        return {
            str(acc.id): title
            for acc in accumulators
            if (title := _accumulator_display_title(acc, mantras_by_id))
        }

    if item_type == RestrictedItemType.GROUP_ACCUMULATOR:
        rows = (
            db.query(GroupAccumulator.id, GroupAccumulator.title)
            .filter(
                GroupAccumulator.id.in_(ids),
                GroupAccumulator.deleted_at.is_(None),
            )
            .all()
        )
        return {
            str(row.id): row.title.strip()
            for row in rows
            if row.title and row.title.strip()
        }

    if item_type == RestrictedItemType.RECITATION_COLLECTION:
        rows = (
            db.query(RecitationCollection.id, RecitationCollection.name)
            .filter(RecitationCollection.id.in_(ids))
            .all()
        )
        return {str(row.id): row.name for row in rows if row.name}

    if item_type == RestrictedItemType.RECITATION:
        return _resolve_recitation_titles(item_ids=ids)

    return {}


def _get_ordered_recitations_response(**kwargs):
    from pecha_api.recitations.order.recitation_order_loader import (
        get_ordered_recitations_response,
    )

    return get_ordered_recitations_response(**kwargs)


def _resolve_recitation_titles(*, item_ids: Sequence[str]) -> Dict[str, str]:
    wanted = {str(item_id) for item_id in item_ids}
    found: Dict[str, str] = {}
    for language in ("en", "bo"):
        try:
            response = _get_ordered_recitations_response(
                language=language,
                search=None,
                skip=0,
                limit=10_000,
            )
        except (OSError, ValueError, TypeError, KeyError, AttributeError, HTTPException):
            continue
        for recitation in response.recitations:
            text_id = str(recitation.text_id)
            if text_id in wanted and text_id not in found and recitation.title:
                found[text_id] = recitation.title.strip()
        if len(found) == len(wanted):
            break
    return found


def search_restriction_candidates(
    db: Session,
    *,
    item_type: RestrictedItemType,
    search: Optional[str],
    skip: int,
    limit: int,
) -> Tuple[List[ChinaRestrictionCandidateDTO], int]:
    term = search.strip() if search and search.strip() else None

    if item_type == RestrictedItemType.PLAN:
        return _search_plans(db=db, term=term, skip=skip, limit=limit)
    if item_type == RestrictedItemType.SERIES:
        return _search_series(db=db, term=term, skip=skip, limit=limit)
    if item_type == RestrictedItemType.GROUP:
        return _search_groups(db=db, term=term, skip=skip, limit=limit)
    if item_type == RestrictedItemType.MANTRA:
        return _search_mantras(db=db, term=term, skip=skip, limit=limit)
    if item_type == RestrictedItemType.ACCUMULATOR:
        return _search_accumulators(db=db, term=term, skip=skip, limit=limit)
    if item_type == RestrictedItemType.GROUP_ACCUMULATOR:
        return _search_group_accumulators(db=db, term=term, skip=skip, limit=limit)
    if item_type == RestrictedItemType.RECITATION_COLLECTION:
        return _search_recitation_collections(db=db, term=term, skip=skip, limit=limit)
    if item_type == RestrictedItemType.RECITATION:
        return _search_recitations(term=term, skip=skip, limit=limit)
    return [], 0


def _search_plans(
    db: Session, *, term: Optional[str], skip: int, limit: int
) -> Tuple[List[ChinaRestrictionCandidateDTO], int]:
    query = db.query(Plan).filter(Plan.deleted_at.is_(None))
    if term:
        query = query.filter(Plan.title.ilike(f"%{term}%"))
    total = query.count()
    rows = query.order_by(Plan.created_at.desc()).offset(skip).limit(limit).all()
    return [
        ChinaRestrictionCandidateDTO(id=str(row.id), title=row.title or "Untitled plan")
        for row in rows
    ], total


def _search_series(
    db: Session, *, term: Optional[str], skip: int, limit: int
) -> Tuple[List[ChinaRestrictionCandidateDTO], int]:
    filters = [Series.deleted_at.is_(None)]
    if term:
        filters.append(
            exists(
                select(1).where(
                    SeriesMetadata.series_id == Series.id,
                    or_(
                        SeriesMetadata.title.ilike(f"%{term}%"),
                        SeriesMetadata.sub_title.ilike(f"%{term}%"),
                    ),
                )
            )
        )
    query = (
        db.query(Series)
        .options(selectinload(Series.metadata_entries))
        .filter(*filters)
    )
    total = query.count()
    rows = query.order_by(Series.created_at.desc()).offset(skip).limit(limit).all()
    return [
        ChinaRestrictionCandidateDTO(
            id=str(row.id),
            title=_pick_metadata_text(row.metadata_entries or []) or "Untitled series",
        )
        for row in rows
    ], total


def _search_groups(
    db: Session, *, term: Optional[str], skip: int, limit: int
) -> Tuple[List[ChinaRestrictionCandidateDTO], int]:
    filters = [AuthorGroup.deleted_at.is_(None)]
    if term:
        filters.append(
            exists(
                select(1).where(
                    AuthorGroupMetadata.group_id == AuthorGroup.id,
                    or_(
                        AuthorGroupMetadata.title.ilike(f"%{term}%"),
                        AuthorGroupMetadata.sub_title.ilike(f"%{term}%"),
                    ),
                )
            )
        )
    query = (
        db.query(AuthorGroup)
        .options(selectinload(AuthorGroup.metadata_entries))
        .filter(*filters)
    )
    total = query.count()
    rows = (
        query.order_by(AuthorGroup.created_at.desc()).offset(skip).limit(limit).all()
    )
    return [
        ChinaRestrictionCandidateDTO(
            id=str(row.id),
            title=_pick_metadata_text(row.metadata_entries or []) or "Untitled group",
            subtitle=row.slug,
        )
        for row in rows
    ], total


def _search_mantras(
    db: Session, *, term: Optional[str], skip: int, limit: int
) -> Tuple[List[ChinaRestrictionCandidateDTO], int]:
    query = db.query(Mantra).options(selectinload(Mantra.metadata_entries))
    if term:
        like = f"%{term}%"
        query = query.filter(
            exists(
                select(1).where(
                    MantraMetadata.mantra_id == Mantra.id,
                    or_(
                        func.coalesce(MantraMetadata.title, "").ilike(like),
                        func.coalesce(MantraMetadata.mantra, "").ilike(like),
                        func.coalesce(MantraMetadata.pronunciation, "").ilike(like),
                    ),
                )
            )
        )
    total = query.count()
    rows = query.order_by(Mantra.created_at.desc()).offset(skip).limit(limit).all()
    return [
        ChinaRestrictionCandidateDTO(
            id=str(row.id),
            title=_mantra_display_title(row) or "Untitled mantra",
        )
        for row in rows
    ], total


def _search_accumulators(
    db: Session, *, term: Optional[str], skip: int, limit: int
) -> Tuple[List[ChinaRestrictionCandidateDTO], int]:
    query = (
        db.query(Accumulator)
        .options(selectinload(Accumulator.metadata_entries))
        .filter(
            Accumulator.type == AccumulatorType.PRESET,
            Accumulator.deleted_at.is_(None),
        )
    )
    if term:
        like = f"%{term}%"
        matching_mantra_ids = db.query(MantraMetadata.mantra_id).filter(
            or_(
                func.coalesce(MantraMetadata.mantra, "").ilike(like),
                func.coalesce(MantraMetadata.title, "").ilike(like),
                func.coalesce(MantraMetadata.pronunciation, "").ilike(like),
            )
        )
        matching_acc_ids = db.query(AccumulatorMetadata.accumulator_id).filter(
            AccumulatorMetadata.name.ilike(like)
        )
        query = query.filter(
            or_(
                Accumulator.mantra_id.in_(matching_mantra_ids),
                Accumulator.id.in_(matching_acc_ids),
            )
        )
    total = query.count()
    rows = (
        query.order_by(Accumulator.created_at.desc()).offset(skip).limit(limit).all()
    )
    mantra_ids = [row.mantra_id for row in rows if row.mantra_id is not None]
    mantras_by_id = get_mantras_by_ids(db, mantra_ids)
    return [
        ChinaRestrictionCandidateDTO(
            id=str(row.id),
            title=_accumulator_display_title(row, mantras_by_id) or "Untitled preset",
        )
        for row in rows
    ], total


def _search_group_accumulators(
    db: Session, *, term: Optional[str], skip: int, limit: int
) -> Tuple[List[ChinaRestrictionCandidateDTO], int]:
    query = db.query(GroupAccumulator).filter(GroupAccumulator.deleted_at.is_(None))
    if term:
        query = query.filter(GroupAccumulator.title.ilike(f"%{term}%"))
    total = query.count()
    rows = (
        query.order_by(GroupAccumulator.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        ChinaRestrictionCandidateDTO(
            id=str(row.id),
            title=(row.title.strip() if row.title and row.title.strip() else "Untitled group accumulator"),
        )
        for row in rows
    ], total


def _search_recitation_collections(
    db: Session, *, term: Optional[str], skip: int, limit: int
) -> Tuple[List[ChinaRestrictionCandidateDTO], int]:
    query = db.query(RecitationCollection)
    if term:
        query = query.filter(RecitationCollection.name.ilike(f"%{term}%"))
    total = query.count()
    rows = (
        query.order_by(RecitationCollection.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        ChinaRestrictionCandidateDTO(id=str(row.id), title=row.name or "Untitled collection")
        for row in rows
    ], total


def _search_recitations(
    *, term: Optional[str], skip: int, limit: int
) -> Tuple[List[ChinaRestrictionCandidateDTO], int]:
    try:
        response = _get_ordered_recitations_response(
            language="en",
            search=term,
            skip=skip,
            limit=limit,
        )
    except (OSError, ValueError, TypeError, KeyError, AttributeError, HTTPException):
        return [], 0

    items: List[ChinaRestrictionCandidateDTO] = [
        ChinaRestrictionCandidateDTO(
            id=str(recitation.text_id),
            title=recitation.title or "Untitled recitation",
        )
        for recitation in response.recitations
    ]
    return items, response.total
