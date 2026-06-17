from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import asc, delete, func, nulls_last, select
from sqlalchemy.orm import Session, selectinload

from pecha_api.plans.plans_enums import PlanStatus
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.tags.tag_model import Tag, plan_tags, tag_segments


def _attach_segment_ids(db: Session, tags: List[Tag]) -> None:
    if not tags:
        return
    segment_ids_map = get_segment_ids_map_for_tags(db=db, tag_ids=[tag.id for tag in tags])
    for tag in tags:
        tag.segment_ids = segment_ids_map.get(tag.id, [])


def _tag_order_clauses():
    return (
        Tag.featured.desc(),
        nulls_last(asc(Tag.display_order)),
        Tag.name.asc(),
    )


def get_next_tag_display_order(db: Session) -> int:
    result = (
        db.query(func.max(Tag.display_order))
        .filter(Tag.deleted_at.is_(None))
        .scalar()
    )
    return (result or 0) + 1


def get_segment_ids_map_for_tags(db: Session, tag_ids: List[UUID]) -> Dict[UUID, List[UUID]]:
    if not tag_ids:
        return {}
    rows = db.execute(
        select(tag_segments.c.tag_id, tag_segments.c.segment_id).where(
            tag_segments.c.tag_id.in_(tag_ids)
        )
    ).all()
    mapping: Dict[UUID, List[UUID]] = {tag_id: [] for tag_id in tag_ids}
    for tag_id, segment_id in rows:
        mapping[tag_id].append(segment_id)
    return mapping


def get_tag_by_id(db: Session, tag_id: UUID, include_deleted: bool = False) -> Optional[Tag]:
    query = db.query(Tag).options(selectinload(Tag.plans)).filter(Tag.id == tag_id)
    if not include_deleted:
        query = query.filter(Tag.deleted_at.is_(None))
    tag = query.first()
    if tag:
        _attach_segment_ids(db=db, tags=[tag])
    return tag


def get_tag_by_name(db: Session, name: str) -> Optional[Tag]:
    return (
        db.query(Tag)
        .filter(Tag.deleted_at.is_(None), func.lower(Tag.name) == name.lower())
        .first()
    )


def get_tags_paginated(
    db: Session,
    search: Optional[str],
    skip: int,
    limit: int,
) -> Tuple[List[Tag], int]:
    query = db.query(Tag).options(selectinload(Tag.plans)).filter(Tag.deleted_at.is_(None))
    if search:
        query = query.filter(Tag.name.ilike(f"%{search}%"))
    total = query.count()
    rows = (
        query.order_by(*_tag_order_clauses())
        .offset(skip)
        .limit(limit)
        .all()
    )
    _attach_segment_ids(db=db, tags=rows)
    return rows, total


def save_tag(db: Session, tag: Tag) -> Tag:
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


def update_tag_row(db: Session, tag: Tag) -> Tag:
    db.commit()
    db.refresh(tag)
    return tag


def soft_delete_tag(db: Session, tag: Tag, deleted_by: str) -> None:
    tag.deleted_at = datetime.now(timezone.utc)
    tag.deleted_by = deleted_by
    db.commit()


def get_tags_by_ids(db: Session, tag_ids: List[UUID]) -> List[Tag]:
    if not tag_ids:
        return []
    return (
        db.query(Tag)
        .filter(Tag.id.in_(tag_ids), Tag.deleted_at.is_(None))
        .all()
    )


def set_tag_plans(db: Session, tag: Tag, plan_ids: List[UUID]) -> Tag:
    plans = db.query(Plan).filter(Plan.id.in_(plan_ids), Plan.deleted_at.is_(None)).all() if plan_ids else []
    tag.plans = plans
    db.commit()
    db.refresh(tag)
    return tag


def set_tag_segments(db: Session, tag: Tag, segment_ids: List[UUID]) -> Tag:
    unique_segment_ids = list(dict.fromkeys(segment_ids))
    db.execute(delete(tag_segments).where(tag_segments.c.tag_id == tag.id))
    if unique_segment_ids:
        rows = [{"tag_id": tag.id, "segment_id": segment_id} for segment_id in unique_segment_ids]
        db.execute(tag_segments.insert(), rows)
    db.commit()
    db.refresh(tag)
    tag.segment_ids = unique_segment_ids
    return tag


def set_plan_tags(db: Session, plan: Plan, tag_ids: Optional[List[UUID]]) -> Plan:
    if tag_ids is None:
        return plan
    tags = get_tags_by_ids(db=db, tag_ids=tag_ids)
    plan.tag_list = tags
    db.commit()
    db.refresh(plan)
    return plan


def get_published_tags_for_language(db: Session, language: str) -> List[Tag]:
    return (
        db.query(Tag)
        .join(plan_tags, plan_tags.c.tag_id == Tag.id)
        .join(Plan, Plan.id == plan_tags.c.plan_id)
        .filter(
            Tag.deleted_at.is_(None),
            Plan.deleted_at.is_(None),
            Plan.status == PlanStatus.PUBLISHED,
            Plan.language == language,
        )
        .distinct()
        .order_by(*_tag_order_clauses())
        .all()
    )


def get_all_tags_paginated(
    db: Session,
    featured: Optional[bool],
    search: Optional[str],
    skip: int,
    limit: int,
) -> Tuple[List[Tag], int]:
    query = db.query(Tag).filter(Tag.deleted_at.is_(None))
    if featured is not None:
        query = query.filter(Tag.featured == featured)
    if search:
        query = query.filter(Tag.name.ilike(f"%{search}%"))

    total = query.count()
    rows = (
        query.order_by(*_tag_order_clauses())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rows, total
