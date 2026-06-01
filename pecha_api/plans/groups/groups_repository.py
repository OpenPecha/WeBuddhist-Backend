from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy import and_, delete, exists, func, or_, select
from sqlalchemy.orm import Session, selectinload

from pecha_api.plans.groups.groups_models import (
    AuthorGroup,
    AuthorGroupInvite,
    AuthorGroupMember,
    AuthorGroupMetadata,
    AuthorGroupSocialLink,
    author_group_followers,
    author_group_plans,
    author_group_series,
    author_group_tags,
)
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.series.series_model import Series
from pecha_api.plans.tags.tag_model import Tag


def _map_entity_ids_to_first_group_id(
    db: Session,
    entity_ids: Sequence[UUID],
    entity_id_column,
    group_id_column,
) -> Dict[UUID, UUID]:
    if not entity_ids:
        return {}
    rows = (
        db.execute(
            select(entity_id_column, group_id_column)
            .where(entity_id_column.in_(entity_ids))
            .order_by(entity_id_column, group_id_column)
        )
        .all()
    )
    group_id_by_entity_id: Dict[UUID, UUID] = {}
    for entity_id, group_id in rows:
        if entity_id not in group_id_by_entity_id:
            group_id_by_entity_id[entity_id] = group_id
    return group_id_by_entity_id


def get_group_ids_by_plan_ids(db: Session, plan_ids: Sequence[UUID]) -> Dict[UUID, UUID]:
    return _map_entity_ids_to_first_group_id(
        db=db,
        entity_ids=plan_ids,
        entity_id_column=author_group_plans.c.plan_id,
        group_id_column=author_group_plans.c.group_id,
    )


def get_group_id_for_plan(db: Session, plan_id: UUID) -> Optional[UUID]:
    return get_group_ids_by_plan_ids(db=db, plan_ids=[plan_id]).get(plan_id)


def get_group_ids_by_series_ids(db: Session, series_ids: Sequence[UUID]) -> Dict[UUID, UUID]:
    return _map_entity_ids_to_first_group_id(
        db=db,
        entity_ids=series_ids,
        entity_id_column=author_group_series.c.series_id,
        group_id_column=author_group_series.c.group_id,
    )


def get_group_id_for_series(db: Session, series_id: UUID) -> Optional[UUID]:
    return get_group_ids_by_series_ids(db=db, series_ids=[series_id]).get(series_id)


def get_group_by_id(db: Session, group_id: UUID) -> Optional[AuthorGroup]:
    return (
        db.query(AuthorGroup)
        .options(
            selectinload(AuthorGroup.metadata_entries),
            selectinload(AuthorGroup.members).selectinload(AuthorGroupMember.author),
            selectinload(AuthorGroup.social_links),
            selectinload(AuthorGroup.tags),
            selectinload(AuthorGroup.plans).selectinload(Plan.tag_list),
            selectinload(AuthorGroup.plans).selectinload(Plan.author),
            selectinload(AuthorGroup.series).selectinload(Series.metadata_entries),
        )
        .filter(AuthorGroup.id == group_id, AuthorGroup.deleted_at.is_(None))
        .first()
    )


def get_group_by_slug(db: Session, slug: str) -> Optional[AuthorGroup]:
    return (
        db.query(AuthorGroup)
        .filter(AuthorGroup.slug == slug, AuthorGroup.deleted_at.is_(None))
        .first()
    )


def get_group_member(
    db: Session,
    group_id: UUID,
    author_id: UUID,
) -> Optional[AuthorGroupMember]:
    return (
        db.query(AuthorGroupMember)
        .options(selectinload(AuthorGroupMember.author))
        .filter(
            AuthorGroupMember.group_id == group_id,
            AuthorGroupMember.author_id == author_id,
        )
        .first()
    )


def get_owner_count(db: Session, group_id: UUID) -> int:
    return (
        db.query(func.count(AuthorGroupMember.id))
        .filter(
            AuthorGroupMember.group_id == group_id,
            AuthorGroupMember.role == "OWNER",
        )
        .scalar()
        or 0
    )


def get_groups_paginated(
    db: Session,
    skip: int,
    limit: int,
    search: Optional[str] = None,
    language: Optional[str] = None,
    tag_id: Optional[UUID] = None,
    group_ids: Optional[Sequence[UUID]] = None,
    public_only: bool = True,
) -> Tuple[List[AuthorGroup], int]:
    filters = [AuthorGroup.deleted_at.is_(None)]
    if public_only:
        filters.append(AuthorGroup.is_public.is_(True))
    if language:
        filters.append(
            exists(
                select(1).where(
                    AuthorGroupMetadata.group_id == AuthorGroup.id,
                    AuthorGroupMetadata.language == language.upper(),
                )
            )
        )
    if search:
        filters.append(
            exists(
                select(1).where(
                    AuthorGroupMetadata.group_id == AuthorGroup.id,
                    or_(
                        AuthorGroupMetadata.title.ilike(f"%{search}%"),
                        AuthorGroupMetadata.description.ilike(f"%{search}%"),
                    ),
                )
            )
        )
    if tag_id:
        filters.append(
            exists(
                select(1).where(
                    and_(
                        author_group_tags.c.group_id == AuthorGroup.id,
                        author_group_tags.c.tag_id == tag_id,
                    )
                )
            )
        )
    if group_ids is not None:
        if not group_ids:
            return [], 0
        filters.append(AuthorGroup.id.in_(group_ids))

    query = (
        db.query(AuthorGroup)
        .options(
            selectinload(AuthorGroup.metadata_entries),
            selectinload(AuthorGroup.members),
            selectinload(AuthorGroup.tags),
        )
        .filter(*filters)
    )
    total = query.count()
    groups = query.order_by(AuthorGroup.created_at.desc()).offset(skip).limit(limit).all()
    return groups, total


def create_group(
    db: Session,
    group: AuthorGroup,
    metadata_entries: List[AuthorGroupMetadata],
    owner_member: AuthorGroupMember,
) -> AuthorGroup:
    db.add(group)
    db.flush()
    for entry in metadata_entries:
        entry.group_id = group.id
        db.add(entry)
    owner_member.group_id = group.id
    db.add(owner_member)
    db.commit()
    db.refresh(group)
    return group


def replace_group_metadata(
    db: Session,
    group_id: UUID,
    metadata_entries: List[AuthorGroupMetadata],
) -> None:
    db.execute(delete(AuthorGroupMetadata).where(AuthorGroupMetadata.group_id == group_id))
    for entry in metadata_entries:
        entry.group_id = group_id
        db.add(entry)
    db.flush()


def replace_group_social_links(
    db: Session,
    group_id: UUID,
    social_links: List[AuthorGroupSocialLink],
) -> None:
    db.execute(delete(AuthorGroupSocialLink).where(AuthorGroupSocialLink.group_id == group_id))
    for link in social_links:
        link.group_id = group_id
        db.add(link)
    db.flush()


def replace_group_relation_ids(
    db: Session,
    table,
    group_id: UUID,
    column_name: str,
    ids: List[UUID],
) -> None:
    db.execute(delete(table).where(table.c.group_id == group_id))
    if not ids:
        return
    rows = [{"group_id": group_id, column_name: item_id} for item_id in ids]
    db.execute(table.insert(), rows)


def set_group_member_role(
    db: Session,
    member: AuthorGroupMember,
    role: str,
    updated_by: str,
) -> AuthorGroupMember:
    member.role = role
    member.updated_at = datetime.now(timezone.utc)
    member.updated_by = updated_by
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def remove_group_member(
    db: Session,
    member: AuthorGroupMember,
) -> None:
    db.delete(member)
    db.commit()


def create_group_invite(db: Session, invite: AuthorGroupInvite) -> AuthorGroupInvite:
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


def get_invite_by_token_hash(db: Session, token_hash: str) -> Optional[AuthorGroupInvite]:
    return (
        db.query(AuthorGroupInvite)
        .options(selectinload(AuthorGroupInvite.group))
        .filter(AuthorGroupInvite.token_hash == token_hash)
        .first()
    )


def get_invite_by_id(db: Session, invite_id: UUID) -> Optional[AuthorGroupInvite]:
    return db.query(AuthorGroupInvite).filter(AuthorGroupInvite.id == invite_id).first()


def revoke_invite(db: Session, invite: AuthorGroupInvite, revoked_by: str) -> None:
    invite.revoked_at = datetime.now(timezone.utc)
    invite.revoked_by = revoked_by
    db.add(invite)
    db.commit()


def increase_invite_use_count(db: Session, invite: AuthorGroupInvite) -> None:
    invite.uses_count = (invite.uses_count or 0) + 1
    db.add(invite)
    db.commit()


def add_group_member(db: Session, member: AuthorGroupMember) -> AuthorGroupMember:
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def upsert_group_follow(
    db: Session,
    group_id: UUID,
    user_id: UUID,
) -> None:
    exists_row = db.execute(
        select(author_group_followers.c.group_id).where(
            author_group_followers.c.group_id == group_id,
            author_group_followers.c.user_id == user_id,
        )
    ).first()
    if exists_row:
        return
    db.execute(
        author_group_followers.insert().values(
            group_id=group_id,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()


def remove_group_follow(
    db: Session,
    group_id: UUID,
    user_id: UUID,
) -> None:
    db.execute(
        delete(author_group_followers).where(
            author_group_followers.c.group_id == group_id,
            author_group_followers.c.user_id == user_id,
        )
    )
    db.commit()


def get_following_group_ids_by_user(
    db: Session,
    user_id: UUID,
) -> List[UUID]:
    rows = db.execute(
        select(author_group_followers.c.group_id).where(author_group_followers.c.user_id == user_id)
    ).all()
    return [row[0] for row in rows]


def get_followers_count_map(db: Session, group_ids: Sequence[UUID]) -> dict[UUID, int]:
    if not group_ids:
        return {}
    rows = (
        db.query(
            author_group_followers.c.group_id,
            func.count(author_group_followers.c.user_id),
        )
        .filter(author_group_followers.c.group_id.in_(group_ids))
        .group_by(author_group_followers.c.group_id)
        .all()
    )
    return {group_id: int(count or 0) for group_id, count in rows}


def get_tags_by_ids(db: Session, tag_ids: List[UUID]) -> List[Tag]:
    if not tag_ids:
        return []
    return db.query(Tag).filter(Tag.id.in_(tag_ids), Tag.deleted_at.is_(None)).all()


def get_plans_by_ids(db: Session, plan_ids: List[UUID]) -> List[Plan]:
    if not plan_ids:
        return []
    return db.query(Plan).filter(Plan.id.in_(plan_ids), Plan.deleted_at.is_(None)).all()


def get_series_by_ids(db: Session, series_ids: List[UUID]) -> List[Series]:
    if not series_ids:
        return []
    return db.query(Series).filter(Series.id.in_(series_ids), Series.deleted_at.is_(None)).all()


def update_group(db: Session, group: AuthorGroup) -> AuthorGroup:
    # Group is already persistent; db.add() would re-sync relationships and can fail
    # after bulk deletes (e.g. replace_group_metadata) left stale entries in memory.
    db.commit()
    db.refresh(group)
    return group
