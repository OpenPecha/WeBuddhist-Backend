from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy import and_, delete, exists, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from pecha_api.plans.groups.groups_enums import (
    AuthorGroupInviteStatus,
    AuthorGroupJoinRequestStatus,
    AuthorGroupType,
)
from pecha_api.plans.groups.groups_models import (
    AuthorGroup,
    AuthorGroupInvite,
    AuthorGroupJoinRequest,
    AuthorGroupMember,
    AuthorGroupMetadata,
    AuthorGroupSocialLink,
    author_group_followers,
    author_group_joins,
    author_group_tags,
)
from pecha_api.plans.plans_enums import PlanStatus
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.series.series_model import Series
from pecha_api.plans.tags.tag_model import Tag
from pecha_api.plans.users.plan_users_models import SeriesPartner, UserSeriesEnrollment
from pecha_api.users.users_models import Users


def get_group_ids_by_plan_ids(db: Session, plan_ids: Sequence[UUID]) -> Dict[UUID, UUID]:
    if not plan_ids:
        return {}
    rows = (
        db.execute(
            select(Plan.id, Plan.group_id).where(
                Plan.id.in_(plan_ids),
                Plan.group_id.isnot(None),
            )
        )
        .all()
    )
    return dict(rows)


def get_group_id_for_plan(db: Session, plan_id: UUID) -> Optional[UUID]:
    row = db.execute(select(Plan.group_id).where(Plan.id == plan_id)).first()
    return row[0] if row else None


def get_group_ids_by_series_ids(db: Session, series_ids: Sequence[UUID]) -> Dict[UUID, UUID]:
    if not series_ids:
        return {}
    rows = (
        db.execute(
            select(Series.id, Series.group_id).where(
                Series.id.in_(series_ids),
                Series.group_id.isnot(None),
            )
        )
        .all()
    )
    return dict(rows)


def get_group_id_for_series(db: Session, series_id: UUID) -> Optional[UUID]:
    row = db.execute(select(Series.group_id).where(Series.id == series_id)).first()
    return row[0] if row else None


def get_author_group_ids(db: Session, author_id: UUID) -> List[UUID]:
    rows = (
        db.query(AuthorGroupMember.group_id)
        .filter(AuthorGroupMember.author_id == author_id)
        .distinct()
        .all()
    )
    return [row[0] for row in rows]


def get_plans_by_group_id(db: Session, group_id: UUID) -> List[Plan]:
    return (
        db.query(Plan)
        .filter(
            Plan.group_id == group_id,
            Plan.deleted_at.is_(None),
            Plan.series_id.is_(None),
        )
        .all()
    )


def get_standalone_plans_for_group_ids(
    db: Session,
    group_ids: Sequence[UUID],
    limit: int,
    exclude_ids: Optional[Sequence[UUID]] = None,
) -> Tuple[List[Plan], int]:
    """Published plans that are not part of a series, across the given groups."""
    if not group_ids:
        return [], 0
    query = db.query(Plan).filter(
        Plan.group_id.in_(group_ids),
        Plan.deleted_at.is_(None),
        Plan.series_id.is_(None),
        Plan.status == PlanStatus.PUBLISHED,
    )
    if exclude_ids:
        query = query.filter(Plan.id.not_in(exclude_ids))
    total = query.count()
    plans = query.order_by(Plan.created_at.desc(), Plan.id.desc()).limit(limit).all()
    return plans, total


def get_series_partner_id_map_for_group(
    db: Session,
    group_id: UUID,
    series_ids: Sequence[UUID],
) -> Dict[UUID, UUID]:
    if not series_ids:
        return {}
    rows = (
        db.execute(
            select(SeriesPartner.series_id, SeriesPartner.id).where(
                SeriesPartner.group_id == group_id,
                SeriesPartner.series_id.in_(series_ids),
            )
        )
        .all()
    )
    return dict(rows)


def get_user_series_enrollment_partner_map(
    db: Session,
    user_id: UUID,
    series_ids: Sequence[UUID],
) -> Dict[UUID, Optional[UUID]]:
    if not series_ids:
        return {}
    rows = (
        db.execute(
            select(
                UserSeriesEnrollment.series_id,
                UserSeriesEnrollment.series_partner_id,
            ).where(
                UserSeriesEnrollment.user_id == user_id,
                UserSeriesEnrollment.series_id.in_(series_ids),
            )
        )
        .all()
    )
    return dict(rows)


def _clear_user_series_partner_ids_for_group(
    db: Session,
    user_id: UUID,
    group_id: UUID,
) -> int:
    partner_ids = [
        row[0]
        for row in db.execute(
            select(SeriesPartner.id).where(SeriesPartner.group_id == group_id)
        ).all()
    ]
    if not partner_ids:
        return 0

    return (
        db.query(UserSeriesEnrollment)
        .filter(
            UserSeriesEnrollment.user_id == user_id,
            UserSeriesEnrollment.series_partner_id.in_(partner_ids),
        )
        .update(
            {
                UserSeriesEnrollment.series_partner_id: None,
                UserSeriesEnrollment.updated_at: datetime.now(timezone.utc),
            },
            synchronize_session=False,
        )
    )


def clear_user_series_partner_ids_for_group(
    db: Session,
    user_id: UUID,
    group_id: UUID,
) -> int:
    updated_count = _clear_user_series_partner_ids_for_group(
        db=db, user_id=user_id, group_id=group_id
    )
    db.commit()
    return updated_count


def leave_group_membership(
    db: Session,
    user_id: UUID,
    group_id: UUID,
) -> None:
    db.execute(
        delete(author_group_joins).where(
            author_group_joins.c.group_id == group_id,
            author_group_joins.c.user_id == user_id,
        )
    )
    _clear_user_series_partner_ids_for_group(
        db=db, user_id=user_id, group_id=group_id
    )
    db.commit()


def get_series_by_group_id(db: Session, group_id: UUID) -> List[Series]:
    return (
        db.query(Series)
        .outerjoin(
            SeriesPartner,
            and_(
                SeriesPartner.series_id == Series.id,
                SeriesPartner.deleted_at.is_(None),
            ),
        )
        .filter(
            Series.deleted_at.is_(None),
            or_(
                Series.group_id == group_id,
                SeriesPartner.group_id == group_id,
            ),
        )
        .distinct()
        .all()
    )


def get_series_for_group_ids(
    db: Session,
    group_ids: Sequence[UUID],
    limit: int,
    exclude_ids: Optional[Sequence[UUID]] = None,
) -> Tuple[List[Series], int]:
    """Published series owned by the given groups, newest first."""
    if not group_ids:
        return [], 0
    query = db.query(Series).filter(
        Series.group_id.in_(group_ids),
        Series.deleted_at.is_(None),
        Series.status == PlanStatus.PUBLISHED,
    )
    if exclude_ids:
        query = query.filter(Series.id.not_in(exclude_ids))
    total = query.count()
    series_list = query.order_by(Series.created_at.desc(), Series.id.desc()).limit(limit).all()
    return series_list, total


def get_group_by_id(db: Session, group_id: UUID) -> Optional[AuthorGroup]:
    return (
        db.query(AuthorGroup)
        .options(
            selectinload(AuthorGroup.metadata_entries),
            selectinload(AuthorGroup.members).selectinload(AuthorGroupMember.author),
            selectinload(AuthorGroup.social_links),
            selectinload(AuthorGroup.tags).selectinload(Tag.metadata_entries),
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


def get_groups_by_ids(db: Session, group_ids: Sequence[UUID]) -> List[AuthorGroup]:
    if not group_ids:
        return []
    return (
        db.query(AuthorGroup)
        .options(
            selectinload(AuthorGroup.metadata_entries),
            selectinload(AuthorGroup.tags).selectinload(Tag.metadata_entries),
            selectinload(AuthorGroup.members),
        )
        .filter(
            AuthorGroup.id.in_(group_ids),
            AuthorGroup.deleted_at.is_(None),
        )
        .all()
    )


def get_public_group_ids(
    db: Session,
    *,
    exclude_group_ids: Optional[Sequence[UUID]] = None,
) -> List[UUID]:
    """Return IDs of non-deleted public author groups, optionally excluding some."""
    query = db.query(AuthorGroup.id).filter(
        AuthorGroup.deleted_at.is_(None),
        AuthorGroup.is_public.is_(True),
    )
    if exclude_group_ids:
        query = query.filter(AuthorGroup.id.not_in(exclude_group_ids))
    return [row[0] for row in query.all()]


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


def get_member_roles_map(
    db: Session,
    author_id: UUID,
    group_ids: Sequence[UUID],
) -> Dict[UUID, str]:
    """Batch-load the author's role in each group (avoids N detail fetches)."""
    if not group_ids:
        return {}
    rows = (
        db.query(AuthorGroupMember.group_id, AuthorGroupMember.role)
        .filter(
            AuthorGroupMember.author_id == author_id,
            AuthorGroupMember.group_id.in_(list(group_ids)),
        )
        .all()
    )
    return {row.group_id: row.role for row in rows}


def list_group_member_ids_by_roles(
    db: Session,
    group_id: UUID,
    roles: Sequence[str],
) -> List[UUID]:
    """Author IDs holding any of the given roles in a group."""
    if not roles:
        return []
    rows = (
        db.query(AuthorGroupMember.author_id)
        .filter(
            AuthorGroupMember.group_id == group_id,
            AuthorGroupMember.role.in_(list(roles)),
        )
        .all()
    )
    return [row[0] for row in rows]


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
    exclude_group_ids: Optional[Sequence[UUID]] = None,
    is_public: Optional[bool] = None,
    group_type: Optional[AuthorGroupType] = None,
) -> Tuple[List[AuthorGroup], int]:
    filters = [AuthorGroup.deleted_at.is_(None)]
    if is_public is not None:
        filters.append(AuthorGroup.is_public.is_(is_public))
    if group_type is not None:
        filters.append(AuthorGroup.group_type == group_type)
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
                        AuthorGroupMetadata.sub_title.ilike(f"%{search}%"),
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
    if exclude_group_ids:
        filters.append(AuthorGroup.id.not_in(exclude_group_ids))

    query = (
        db.query(AuthorGroup)
        .options(
            selectinload(AuthorGroup.metadata_entries),
            selectinload(AuthorGroup.members),
            selectinload(AuthorGroup.tags).selectinload(Tag.metadata_entries),
        )
        .filter(*filters)

    )
    total = query.count()
    groups = (
        query.order_by(AuthorGroup.is_public.desc(), AuthorGroup.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
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


def get_invite_by_id(
    db: Session,
    invite_id: UUID,
    *,
    load_group: bool = False,
) -> Optional[AuthorGroupInvite]:
    query = db.query(AuthorGroupInvite).filter(AuthorGroupInvite.id == invite_id)
    if load_group:
        query = query.options(selectinload(AuthorGroupInvite.group))
    return query.first()


def list_invites_by_group(
    db: Session,
    group_id: UUID,
    status: Optional[AuthorGroupInviteStatus] = None,
) -> List[AuthorGroupInvite]:
    query = (
        db.query(AuthorGroupInvite)
        .options(selectinload(AuthorGroupInvite.group).selectinload(AuthorGroup.metadata_entries))
        .filter(AuthorGroupInvite.group_id == group_id)
    )
    if status is not None:
        query = query.filter(AuthorGroupInvite.status == status.value)
    return query.order_by(AuthorGroupInvite.created_at.desc()).all()


def list_pending_invites_by_email(db: Session, target_email: str) -> List[AuthorGroupInvite]:
    now = datetime.now(timezone.utc)
    return (
        db.query(AuthorGroupInvite)
        .options(selectinload(AuthorGroupInvite.group).selectinload(AuthorGroup.metadata_entries))
        .filter(
            AuthorGroupInvite.target_email == target_email.lower(),
            AuthorGroupInvite.status == AuthorGroupInviteStatus.PENDING.value,
            AuthorGroupInvite.expires_at > now,
        )
        .order_by(AuthorGroupInvite.created_at.desc())
        .all()
    )


def has_pending_invite(db: Session, group_id: UUID, target_email: str) -> bool:
    now = datetime.now(timezone.utc)
    return (
        db.query(AuthorGroupInvite.id)
        .filter(
            AuthorGroupInvite.group_id == group_id,
            AuthorGroupInvite.target_email == target_email.lower(),
            AuthorGroupInvite.status == AuthorGroupInviteStatus.PENDING.value,
            AuthorGroupInvite.expires_at > now,
        )
        .first()
        is not None
    )


def save_invite(db: Session, invite: AuthorGroupInvite) -> AuthorGroupInvite:
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


def revoke_invite(db: Session, invite: AuthorGroupInvite, revoked_by: str) -> None:
    now = datetime.now(timezone.utc)
    invite.status = AuthorGroupInviteStatus.REVOKED.value
    invite.revoked_at = now
    invite.revoked_by = revoked_by
    db.add(invite)
    db.commit()


def create_group_join_request(
    db: Session,
    join_request: AuthorGroupJoinRequest,
) -> AuthorGroupJoinRequest:
    db.add(join_request)
    db.commit()
    db.refresh(join_request)
    return join_request


def get_join_request_by_id(
    db: Session,
    request_id: UUID,
    *,
    load_group: bool = False,
) -> Optional[AuthorGroupJoinRequest]:
    query = db.query(AuthorGroupJoinRequest).filter(AuthorGroupJoinRequest.id == request_id)
    if load_group:
        query = query.options(
            selectinload(AuthorGroupJoinRequest.group).selectinload(AuthorGroup.metadata_entries)
        )
    return query.first()


def list_join_requests_by_group(
    db: Session,
    group_id: UUID,
    skip: int,
    limit: int,
    status: Optional[AuthorGroupJoinRequestStatus] = None,
) -> Tuple[List[AuthorGroupJoinRequest], int]:
    query = (
        db.query(AuthorGroupJoinRequest)
        .options(selectinload(AuthorGroupJoinRequest.user))
        .filter(AuthorGroupJoinRequest.group_id == group_id)
    )
    if status is not None:
        query = query.filter(AuthorGroupJoinRequest.status == status.value)
    total = query.count()
    rows = (
        query.order_by(AuthorGroupJoinRequest.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rows, total


def has_pending_join_request(db: Session, group_id: UUID, user_id: UUID) -> bool:
    return (
        db.query(AuthorGroupJoinRequest.id)
        .filter(
            AuthorGroupJoinRequest.group_id == group_id,
            AuthorGroupJoinRequest.user_id == user_id,
            AuthorGroupJoinRequest.status == AuthorGroupJoinRequestStatus.PENDING.value,
        )
        .first()
        is not None
    )


def list_pending_join_requests_by_group(
    db: Session,
    group_id: UUID,
) -> List[AuthorGroupJoinRequest]:
    return (
        db.query(AuthorGroupJoinRequest)
        .filter(
            AuthorGroupJoinRequest.group_id == group_id,
            AuthorGroupJoinRequest.status == AuthorGroupJoinRequestStatus.PENDING.value,
        )
        .all()
    )


def save_join_request(
    db: Session,
    join_request: AuthorGroupJoinRequest,
) -> AuthorGroupJoinRequest:
    db.add(join_request)
    db.commit()
    db.refresh(join_request)
    return join_request


def mark_join_request_notification_dispatched(
    db: Session,
    join_request_id: UUID,
    sqs_message_id: str,
    *,
    decision: bool = False,
) -> None:
    join_request = (
        db.query(AuthorGroupJoinRequest)
        .filter(AuthorGroupJoinRequest.id == join_request_id)
        .first()
    )
    if not join_request:
        return
    now = datetime.now(timezone.utc)
    if decision:
        join_request.decision_sqs_message_id = sqs_message_id
        join_request.decision_dispatched_at = now
    else:
        join_request.notification_sqs_message_id = sqs_message_id
        join_request.notification_dispatched_at = now
    db.add(join_request)
    db.commit()


def list_undispatched_join_request_notifications(
    db: Session,
    older_than: datetime,
    limit: int,
) -> List[AuthorGroupJoinRequest]:
    return (
        db.query(AuthorGroupJoinRequest)
        .filter(
            AuthorGroupJoinRequest.notification_sqs_message_id.is_(None),
            AuthorGroupJoinRequest.created_at < older_than,
        )
        .order_by(AuthorGroupJoinRequest.created_at)
        .limit(limit)
        .all()
    )



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


def is_user_following_group(
    db: Session,
    group_id: UUID,
    user_id: UUID,
) -> bool:
    row = db.execute(
        select(author_group_followers.c.group_id).where(
            author_group_followers.c.group_id == group_id,
            author_group_followers.c.user_id == user_id,
        )
    ).first()
    return row is not None


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


def upsert_group_join(
    db: Session,
    group_id: UUID,
    user_id: UUID,
) -> None:
    exists_row = db.execute(
        select(author_group_joins.c.group_id).where(
            author_group_joins.c.group_id == group_id,
            author_group_joins.c.user_id == user_id,
        )
    ).first()
    if exists_row:
        return
    db.execute(
        author_group_joins.insert().values(
            group_id=group_id,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()


def remove_group_join(
    db: Session,
    group_id: UUID,
    user_id: UUID,
) -> None:
    db.execute(
        delete(author_group_joins).where(
            author_group_joins.c.group_id == group_id,
            author_group_joins.c.user_id == user_id,
        )
    )
    db.commit()


def get_joined_group_ids_by_user(
    db: Session,
    user_id: UUID,
) -> List[UUID]:
    rows = db.execute(
        select(author_group_joins.c.group_id).where(author_group_joins.c.user_id == user_id)
    ).all()
    return [row[0] for row in rows]


def is_user_joined_group(
    db: Session,
    group_id: UUID,
    user_id: UUID,
) -> bool:
    row = db.execute(
        select(author_group_joins.c.group_id).where(
            author_group_joins.c.group_id == group_id,
            author_group_joins.c.user_id == user_id,
        )
    ).first()
    return row is not None


def list_group_joiners_paginated(
    db: Session,
    group_id: UUID,
    skip: int,
    limit: int,
) -> Tuple[List[Users], int]:
    query = (
        db.query(Users)
        .join(author_group_joins, Users.id == author_group_joins.c.user_id)
        .filter(author_group_joins.c.group_id == group_id)
    )
    total = query.count()
    users = (
        query.order_by(author_group_joins.c.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return users, total


def get_joiners_count_map(db: Session, group_ids: Sequence[UUID]) -> dict[UUID, int]:
    if not group_ids:
        return {}
    rows = (
        db.query(
            author_group_joins.c.group_id,
            func.count(author_group_joins.c.user_id),
        )
        .filter(author_group_joins.c.group_id.in_(group_ids))
        .group_by(author_group_joins.c.group_id)
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
