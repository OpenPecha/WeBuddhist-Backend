import hashlib
import secrets
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details
from pecha_api.plans.groups.groups_enums import AuthorGroupMemberRole
from pecha_api.plans.groups.groups_models import (
    AuthorGroup,
    AuthorGroupInvite,
    AuthorGroupMember,
    AuthorGroupMetadata,
    AuthorGroupSocialLink,
)
from pecha_api.plans.groups.groups_repository import (
    add_group_member,
    create_group,
    create_group_invite,
    get_followers_count_map,
    get_following_group_ids_by_user,
    get_group_by_id,
    get_group_by_slug,
    get_group_member,
    get_groups_paginated,
    get_invite_by_id,
    get_invite_by_token_hash,
    get_owner_count,
    get_plans_by_ids,
    get_series_by_ids,
    get_tags_by_ids,
    increase_invite_use_count,
    remove_group_follow,
    remove_group_member,
    replace_group_metadata,
    replace_group_relation_ids,
    replace_group_social_links,
    revoke_invite,
    set_group_member_role,
    update_group,
    upsert_group_follow,
)
from pecha_api.plans.groups.groups_response_models import (
    AcceptGroupInviteRequest,
    AuthorGroupDetailDTO,
    AuthorGroupListResponse,
    AuthorGroupMemberDTO,
    AuthorGroupSummaryDTO,
    CreateAuthorGroupRequest,
    CreateGroupInviteRequest,
    GroupInviteCreatedResponse,
    GroupMetadataDTO,
    GroupSocialLinkDTO,
    ReplaceGroupPlansRequest,
    ReplaceGroupSeriesRequest,
    ReplaceGroupSocialLinksRequest,
    ReplaceGroupTagsRequest,
    UpdateAuthorGroupRequest,
    UpdateGroupMemberRoleRequest,
)
from pecha_api.plans.groups.groups_models import (
    author_group_plans,
    author_group_series,
    author_group_tags,
)
from pecha_api.plans.tags.tag_helpers import tags_to_summary_dtos
from pecha_api.users.users_service import validate_and_extract_user_details

GROUP_NOT_FOUND = "Group not found"


class InviteEmailMismatchError(Exception):
    pass


def _to_role_value(role: AuthorGroupMemberRole | str) -> str:
    if hasattr(role, "value"):
        return role.value
    return str(role)


def _metadata_to_dtos(metadata_entries) -> List[GroupMetadataDTO]:
    return [
        GroupMetadataDTO(
            id=item.id,
            title=item.title,
            description=item.description,
            language=item.language,
        )
        for item in sorted(metadata_entries, key=lambda value: value.language)
    ]


def _members_to_dtos(members) -> List[AuthorGroupMemberDTO]:
    return [
        AuthorGroupMemberDTO(
            author_id=member.author_id,
            role=AuthorGroupMemberRole(_to_role_value(member.role)),
            firstname=member.author.first_name,
            lastname=member.author.last_name,
            email=member.author.email,
        )
        for member in members
    ]


def _social_links_to_dtos(links) -> List[GroupSocialLinkDTO]:
    return [GroupSocialLinkDTO(id=link.id, platform=link.platform, url=link.url) for link in links]


def _assert_metadata_valid(metadata_entries: List) -> None:
    if not metadata_entries:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group must have at least one metadata entry",
        )
    seen_languages = set()
    for item in metadata_entries:
        if not item.title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Metadata title is required",
            )
        language = item.language.value if hasattr(item.language, "value") else item.language
        if language in seen_languages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Metadata language must be unique per group",
            )
        seen_languages.add(language)


def _get_member_or_403(db, group_id: UUID, author_id: UUID):
    member = get_group_member(db=db, group_id=group_id, author_id=author_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group",
        )
    return member


def _assert_role_allowed(member: AuthorGroupMember, allowed_roles: List[AuthorGroupMemberRole]):
    role_value = _to_role_value(member.role)
    if role_value not in [_to_role_value(role) for role in allowed_roles]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission for this action",
        )


def _validate_group_links(db, tag_ids: Optional[List[UUID]], series_ids: Optional[List[UUID]], plan_ids: Optional[List[UUID]]) -> None:
    if tag_ids is not None:
        found_tags = get_tags_by_ids(db=db, tag_ids=tag_ids)
        if len(found_tags) != len(set(tag_ids)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more tags do not exist")
    if series_ids is not None:
        found_series = get_series_by_ids(db=db, series_ids=series_ids)
        if len(found_series) != len(set(series_ids)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more series do not exist")
    if plan_ids is not None:
        found_plans = get_plans_by_ids(db=db, plan_ids=plan_ids)
        if len(found_plans) != len(set(plan_ids)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more plans do not exist")


def _group_to_summary(group: AuthorGroup, follower_count: int = 0) -> AuthorGroupSummaryDTO:
    return AuthorGroupSummaryDTO(
        id=group.id,
        slug=group.slug,
        is_public=group.is_public,
        metadata=_metadata_to_dtos(group.metadata_entries),
        tags=tags_to_summary_dtos(group.tags),
        follower_count=follower_count,
        member_count=len(group.members),
    )


def _group_to_detail(group: AuthorGroup, follower_count: int = 0) -> AuthorGroupDetailDTO:
    return AuthorGroupDetailDTO(
        id=group.id,
        slug=group.slug,
        is_public=group.is_public,
        avatar_key=group.avatar_key,
        banner_key=group.banner_key,
        metadata=_metadata_to_dtos(group.metadata_entries),
        members=_members_to_dtos(group.members),
        tags=tags_to_summary_dtos(group.tags),
        social_links=_social_links_to_dtos(group.social_links),
        series_ids=[series.id for series in group.series],
        plan_ids=[plan.id for plan in group.plans],
        follower_count=follower_count,
    )


def create_author_group(token: str, request: CreateAuthorGroupRequest) -> AuthorGroupDetailDTO:
    _assert_metadata_valid(request.metadata)
    author = validate_and_extract_author_details(token=token)

    with SessionLocal() as db:
        if get_group_by_slug(db=db, slug=request.slug):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group slug already exists")

        metadata_entries = [
            AuthorGroupMetadata(
                language=item.language.value,
                title=item.title,
                description=item.description,
            )
            for item in request.metadata
        ]
        group = AuthorGroup(
            slug=request.slug,
            is_public=request.is_public,
            avatar_key=request.avatar_key,
            banner_key=request.banner_key,
            created_by=author.email,
            updated_by=author.email,
        )
        owner_member = AuthorGroupMember(
            author_id=author.id,
            role=AuthorGroupMemberRole.OWNER,
            created_by=author.email,
            updated_by=author.email,
        )
        created = create_group(db=db, group=group, metadata_entries=metadata_entries, owner_member=owner_member)
        loaded = get_group_by_id(db=db, group_id=created.id)
        return _group_to_detail(loaded, follower_count=0)


def update_author_group(token: str, group_id: UUID, request: UpdateAuthorGroupRequest) -> AuthorGroupDetailDTO:
    author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
        if not author.is_admin:
            member = _get_member_or_403(db=db, group_id=group_id, author_id=author.id)
            _assert_role_allowed(member=member, allowed_roles=[AuthorGroupMemberRole.OWNER, AuthorGroupMemberRole.ADMIN, AuthorGroupMemberRole.EDITOR])

        if request.slug is not None and request.slug != group.slug:
            existing = get_group_by_slug(db=db, slug=request.slug)
            if existing and existing.id != group.id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group slug already exists")
            group.slug = request.slug
        if request.is_public is not None:
            group.is_public = request.is_public
        if request.avatar_key is not None:
            group.avatar_key = request.avatar_key
        if request.banner_key is not None:
            group.banner_key = request.banner_key
        if request.metadata is not None:
            _assert_metadata_valid(request.metadata)
            metadata_entries = [
                AuthorGroupMetadata(
                    language=item.language.value,
                    title=item.title,
                    description=item.description,
                )
                for item in request.metadata
            ]
            replace_group_metadata(db=db, group_id=group_id, metadata_entries=metadata_entries)

        group.updated_by = author.email
        group.updated_at = datetime.now(timezone.utc)
        update_group(db=db, group=group)
        loaded = get_group_by_id(db=db, group_id=group_id)
        followers_count = get_followers_count_map(db=db, group_ids=[group_id]).get(group_id, 0)
        return _group_to_detail(group=loaded, follower_count=followers_count)


def get_author_group_detail(group_id: UUID, require_public: bool = True) -> AuthorGroupDetailDTO:
    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
        if require_public and not group.is_public:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
        follower_count = get_followers_count_map(db=db, group_ids=[group_id]).get(group_id, 0)
        return _group_to_detail(group=group, follower_count=follower_count)


def get_cms_group_detail(token: str, group_id: UUID) -> AuthorGroupDetailDTO:
    author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
        if not author.is_admin:
            _get_member_or_403(db=db, group_id=group_id, author_id=author.id)
        follower_count = get_followers_count_map(db=db, group_ids=[group_id]).get(group_id, 0)
        return _group_to_detail(group=group, follower_count=follower_count)


def list_public_groups(
    skip: int,
    limit: int,
    search: Optional[str] = None,
    language: Optional[str] = None,
    tag_id: Optional[UUID] = None,
) -> AuthorGroupListResponse:
    with SessionLocal() as db:
        groups, total = get_groups_paginated(
            db=db,
            skip=skip,
            limit=limit,
            search=search,
            language=language,
            tag_id=tag_id,
            public_only=True,
        )
        group_ids = [group.id for group in groups]
        follower_count_map = get_followers_count_map(db=db, group_ids=group_ids)
        return AuthorGroupListResponse(
            groups=[_group_to_summary(group=item, follower_count=follower_count_map.get(item.id, 0)) for item in groups],
            skip=skip,
            limit=limit,
            total=total,
        )


def list_cms_groups(
    token: str,
    skip: int,
    limit: int,
    search: Optional[str] = None,
    language: Optional[str] = None,
    tag_id: Optional[UUID] = None,
) -> AuthorGroupListResponse:
    author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        group_ids = None
        if not author.is_admin:
            membership_rows = db.query(AuthorGroupMember.group_id).filter(AuthorGroupMember.author_id == author.id).all()
            group_ids = [row.group_id for row in membership_rows]
        groups, total = get_groups_paginated(
            db=db,
            skip=skip,
            limit=limit,
            search=search,
            language=language,
            tag_id=tag_id,
            group_ids=group_ids,
            public_only=False,
        )
        ids = [group.id for group in groups]
        follower_count_map = get_followers_count_map(db=db, group_ids=ids)
        return AuthorGroupListResponse(
            groups=[_group_to_summary(group=item, follower_count=follower_count_map.get(item.id, 0)) for item in groups],
            skip=skip,
            limit=limit,
            total=total,
        )


def replace_group_tags(token: str, group_id: UUID, request: ReplaceGroupTagsRequest) -> AuthorGroupDetailDTO:
    author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
        if not author.is_admin:
            member = _get_member_or_403(db=db, group_id=group_id, author_id=author.id)
            _assert_role_allowed(member=member, allowed_roles=[AuthorGroupMemberRole.OWNER, AuthorGroupMemberRole.ADMIN, AuthorGroupMemberRole.EDITOR])
        _validate_group_links(db=db, tag_ids=request.tag_ids, series_ids=None, plan_ids=None)
        replace_group_relation_ids(db=db, table=author_group_tags, group_id=group_id, column_name="tag_id", ids=request.tag_ids)
        db.commit()
        loaded = get_group_by_id(db=db, group_id=group_id)
        follower_count = get_followers_count_map(db=db, group_ids=[group_id]).get(group_id, 0)
        return _group_to_detail(loaded, follower_count=follower_count)


def replace_group_social_links_by_id(
    token: str,
    group_id: UUID,
    request: ReplaceGroupSocialLinksRequest,
) -> AuthorGroupDetailDTO:
    author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
        if not author.is_admin:
            member = _get_member_or_403(db=db, group_id=group_id, author_id=author.id)
            _assert_role_allowed(member=member, allowed_roles=[AuthorGroupMemberRole.OWNER, AuthorGroupMemberRole.ADMIN, AuthorGroupMemberRole.EDITOR])
        social_links = [AuthorGroupSocialLink(platform=item.platform, url=item.url) for item in request.social_links]
        replace_group_social_links(db=db, group_id=group_id, social_links=social_links)
        db.commit()
        loaded = get_group_by_id(db=db, group_id=group_id)
        follower_count = get_followers_count_map(db=db, group_ids=[group_id]).get(group_id, 0)
        return _group_to_detail(loaded, follower_count=follower_count)


def replace_group_series_by_id(token: str, group_id: UUID, request: ReplaceGroupSeriesRequest) -> AuthorGroupDetailDTO:
    author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
        if not author.is_admin:
            member = _get_member_or_403(db=db, group_id=group_id, author_id=author.id)
            _assert_role_allowed(member=member, allowed_roles=[AuthorGroupMemberRole.OWNER, AuthorGroupMemberRole.ADMIN, AuthorGroupMemberRole.EDITOR])
        _validate_group_links(db=db, tag_ids=None, series_ids=request.series_ids, plan_ids=None)
        replace_group_relation_ids(db=db, table=author_group_series, group_id=group_id, column_name="series_id", ids=request.series_ids)
        db.commit()
        loaded = get_group_by_id(db=db, group_id=group_id)
        follower_count = get_followers_count_map(db=db, group_ids=[group_id]).get(group_id, 0)
        return _group_to_detail(loaded, follower_count=follower_count)


def replace_group_plans_by_id(token: str, group_id: UUID, request: ReplaceGroupPlansRequest) -> AuthorGroupDetailDTO:
    author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
        if not author.is_admin:
            member = _get_member_or_403(db=db, group_id=group_id, author_id=author.id)
            _assert_role_allowed(member=member, allowed_roles=[AuthorGroupMemberRole.OWNER, AuthorGroupMemberRole.ADMIN, AuthorGroupMemberRole.EDITOR])
        _validate_group_links(db=db, tag_ids=None, series_ids=None, plan_ids=request.plan_ids)
        replace_group_relation_ids(db=db, table=author_group_plans, group_id=group_id, column_name="plan_id", ids=request.plan_ids)
        db.commit()
        loaded = get_group_by_id(db=db, group_id=group_id)
        follower_count = get_followers_count_map(db=db, group_ids=[group_id]).get(group_id, 0)
        return _group_to_detail(loaded, follower_count=follower_count)


def follow_group(token: str, group_id: UUID) -> None:
    user = validate_and_extract_user_details(token=token)
    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group or not group.is_public:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
        upsert_group_follow(db=db, group_id=group_id, user_id=user.id)


def unfollow_group(token: str, group_id: UUID) -> None:
    user = validate_and_extract_user_details(token=token)
    with SessionLocal() as db:
        remove_group_follow(db=db, group_id=group_id, user_id=user.id)


def list_followed_groups(token: str, skip: int, limit: int) -> AuthorGroupListResponse:
    user = validate_and_extract_user_details(token=token)
    with SessionLocal() as db:
        group_ids = get_following_group_ids_by_user(db=db, user_id=user.id)
        groups, total = get_groups_paginated(
            db=db,
            skip=skip,
            limit=limit,
            group_ids=group_ids,
            public_only=False,
        )
        follower_count_map = get_followers_count_map(db=db, group_ids=[group.id for group in groups])
        return AuthorGroupListResponse(
            groups=[_group_to_summary(group=item, follower_count=follower_count_map.get(item.id, 0)) for item in groups],
            skip=skip,
            limit=limit,
            total=total,
        )


def create_group_member_invite(
    token: str,
    group_id: UUID,
    request: CreateGroupInviteRequest,
) -> GroupInviteCreatedResponse:
    author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
        if not author.is_admin:
            member = _get_member_or_403(db=db, group_id=group_id, author_id=author.id)
            _assert_role_allowed(member=member, allowed_roles=[AuthorGroupMemberRole.OWNER, AuthorGroupMemberRole.ADMIN])

        raw_token = secrets.token_urlsafe(48)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        invite = AuthorGroupInvite(
            group_id=group_id,
            target_email=request.target_email.lower(),
            role=request.role,
            token_hash=token_hash,
            expires_at=request.expires_at,
            max_uses=request.max_uses,
            created_by=author.email,
        )
        created = create_group_invite(db=db, invite=invite)
        return GroupInviteCreatedResponse(
            invite_id=created.id,
            token=raw_token,
            target_email=created.target_email,
            role=AuthorGroupMemberRole(_to_role_value(created.role)),
            expires_at=created.expires_at,
            max_uses=created.max_uses,
        )


def _validate_invite_acceptance(invite: AuthorGroupInvite) -> None:
    now = datetime.now(timezone.utc)
    if invite.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite has been revoked")
    if invite.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite has expired")
    if invite.uses_count >= invite.max_uses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite usage limit exceeded")


def accept_group_invite(token: str, request: AcceptGroupInviteRequest) -> AuthorGroupDetailDTO:
    author = validate_and_extract_author_details(token=token)
    token_hash = hashlib.sha256(request.token.encode("utf-8")).hexdigest()
    with SessionLocal() as db:
        invite = get_invite_by_token_hash(db=db, token_hash=token_hash)
        if not invite:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
        _validate_invite_acceptance(invite=invite)
        if author.email.lower() != invite.target_email.lower():
            raise InviteEmailMismatchError("This invite was sent to a different email address.")

        group = get_group_by_id(db=db, group_id=invite.group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)

        existing_member = get_group_member(db=db, group_id=group.id, author_id=author.id)
        if existing_member is None:
            add_group_member(
                db=db,
                member=AuthorGroupMember(
                    group_id=group.id,
                    author_id=author.id,
                    role=invite.role,
                    created_by=author.email,
                ),
            )
        increase_invite_use_count(db=db, invite=invite)
        loaded = get_group_by_id(db=db, group_id=group.id)
        follower_count = get_followers_count_map(db=db, group_ids=[group.id]).get(group.id, 0)
        return _group_to_detail(loaded, follower_count=follower_count)


def revoke_group_invite(token: str, group_id: UUID, invite_id: UUID) -> None:
    author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
        if not author.is_admin:
            member = _get_member_or_403(db=db, group_id=group_id, author_id=author.id)
            _assert_role_allowed(member=member, allowed_roles=[AuthorGroupMemberRole.OWNER, AuthorGroupMemberRole.ADMIN])

        invite = get_invite_by_id(db=db, invite_id=invite_id)
        if not invite or invite.group_id != group_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
        revoke_invite(db=db, invite=invite, revoked_by=author.email)


def update_group_member_role(
    token: str,
    group_id: UUID,
    author_id: UUID,
    request: UpdateGroupMemberRoleRequest,
) -> AuthorGroupDetailDTO:
    current_author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
        if not current_author.is_admin:
            current_member = _get_member_or_403(db=db, group_id=group_id, author_id=current_author.id)
            _assert_role_allowed(current_member, [AuthorGroupMemberRole.OWNER, AuthorGroupMemberRole.ADMIN])

        target_member = get_group_member(db=db, group_id=group_id, author_id=author_id)
        if not target_member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group member not found")

        target_role = _to_role_value(target_member.role)
        requested_role = _to_role_value(request.role)
        if target_role == "OWNER" and requested_role != "OWNER":
            owner_count = get_owner_count(db=db, group_id=group_id)
            if owner_count <= 1:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one OWNER must always remain")

        set_group_member_role(db=db, member=target_member, role=request.role.value, updated_by=current_author.email)
        loaded = get_group_by_id(db=db, group_id=group_id)
        follower_count = get_followers_count_map(db=db, group_ids=[group_id]).get(group_id, 0)
        return _group_to_detail(loaded, follower_count=follower_count)


def delete_group_member(token: str, group_id: UUID, author_id: UUID) -> None:
    current_author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
        if not current_author.is_admin:
            current_member = _get_member_or_403(db=db, group_id=group_id, author_id=current_author.id)
            _assert_role_allowed(current_member, [AuthorGroupMemberRole.OWNER, AuthorGroupMemberRole.ADMIN])

        member = get_group_member(db=db, group_id=group_id, author_id=author_id)
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group member not found")
        if _to_role_value(member.role) == "OWNER":
            owner_count = get_owner_count(db=db, group_id=group_id)
            if owner_count <= 1:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OWNER cannot be removed if they are the last owner")
        remove_group_member(db=db, member=member)
