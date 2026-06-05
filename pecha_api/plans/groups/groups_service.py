from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from pecha_api.config import get, get_int
from pecha_api.db.database import SessionLocal
from pecha_api.uploads.S3_utils import generate_presigned_access_url
from pecha_api.plans.authors.plan_authors_repository import get_author_by_email
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details, validate_cms_author_details
from pecha_api.plans.shared.permissions import is_reviewer, is_super_admin, require_cms_write_access
from pecha_api.notification.notification_repository import mark_notifications_read_by_reference
from pecha_api.notification.notification_service import create_notification_record
from pecha_api.plans.groups.group_invite_email import send_group_invitation_email
from pecha_api.plans.groups.groups_enums import AuthorGroupInviteStatus, AuthorGroupMemberRole
from pecha_api.plans.groups.groups_models import (
    AuthorGroup,
    AuthorGroupInvite,
    AuthorGroupMember,
    AuthorGroupMetadata,
    AuthorGroupSocialLink,
)
from pecha_api.plans.plans_enums import PlanStatus
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.cms.cms_plans_repository import get_plans_with_aggregates_by_ids
from pecha_api.plans.plans_response_models import AuthorDTO, PlanDTO, PlanWithAggregates
from pecha_api.plans.series.series_model import Series
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
    get_owner_count,
    get_plans_by_group_id,
    get_plans_by_ids,
    get_series_by_group_id,
    has_pending_invite,
    list_invites_by_group,
    list_pending_invites_by_email,
    get_series_by_ids,
    get_tags_by_ids,
    save_invite,
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
from pecha_api.plans.series.series_repository import get_active_plan_count_map_by_series_ids
from pecha_api.plans.series.series_response_models import SeriesListItemDTO
from pecha_api.plans.series.series_service import _series_to_list_item_dto
from pecha_api.plans.shared.metadata_utils import format_metadata_response
from pecha_api.plans.groups.groups_response_models import (
    AuthorGroupDetailDTO,
    AuthorGroupListResponse,
    AuthorGroupMemberDTO,
    AuthorGroupSummaryDTO,
    CreateAuthorGroupRequest,
    CreateGroupInviteRequest,
    GroupInviteCreatedResponse,
    GroupInviteDTO,
    GroupInviteListResponse,
    GroupMetadataDTO,
    GroupSocialLinkDTO,
    PublicAuthorGroupDetailDTO,
    PublicAuthorGroupListResponse,
    PublicAuthorGroupSummaryDTO,
    ReplaceGroupPlansRequest,
    ReplaceGroupSeriesRequest,
    ReplaceGroupSocialLinksRequest,
    ReplaceGroupTagsRequest,
    UpdateAuthorGroupRequest,
    UpdateGroupMemberRoleRequest,
)
from pecha_api.plans.groups.groups_models import author_group_tags
from pecha_api.plans.tags.tag_helpers import tags_to_summary_dtos
from pecha_api.users.users_service import validate_and_extract_user_details

GROUP_NOT_FOUND = "Group not found"
INVITE_NOT_FOUND = "Invite not found"
OWNER_ROLE_NOT_ASSIGNABLE = (
    "The OWNER role cannot be assigned via invite or role change; use transfer ownership"
)
GROUP_ALREADY_HAS_OWNER = "This group already has an owner"
NOTIFICATION_CATEGORY_GROUP_INVITE = "group_invite"


def _to_role_value(role: AuthorGroupMemberRole | str) -> str:
    if hasattr(role, "value"):
        return role.value
    return str(role)


def _generate_group_asset_url(asset_key: Optional[str]) -> Optional[str]:
    if not asset_key:
        return None
    return generate_presigned_access_url(
        bucket_name=get("AWS_BUCKET_NAME"),
        s3_key=asset_key,
    )


def _optional_metadata_str(value) -> Optional[str]:
    return value if isinstance(value, str) else None


def _metadata_to_dtos(metadata_entries, language: Optional[str] = None) -> List[GroupMetadataDTO]:
    if language:
        language_upper = language.upper()
        metadata_entries = [
            item for item in metadata_entries
            if _language_value(item.language).upper() == language_upper
        ]
    return [
        GroupMetadataDTO(
            id=item.id,
            title=item.title,
            sub_title=_optional_metadata_str(getattr(item, "sub_title", None)),
            description=item.description,
            language=_language_value(item.language),
        )
        for item in sorted(metadata_entries, key=lambda value: value.language)
    ]


def _metadata_response(metadata_entries, language: Optional[str] = None):
    return format_metadata_response(
        _metadata_to_dtos(metadata_entries, language=language),
        language=language,
    )


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


def _group_tag_names(tags) -> List[str]:
    if not tags:
        return []
    active = [tag for tag in tags if tag.deleted_at is None]
    return sorted((tag.name for tag in active), key=str.lower)


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


_GROUP_SETTINGS_ROLES = [AuthorGroupMemberRole.OWNER, AuthorGroupMemberRole.ADMIN]
_MEMBER_MANAGEMENT_ROLES = [AuthorGroupMemberRole.OWNER, AuthorGroupMemberRole.ADMIN]
_ADMIN_INVITE_ROLE = AuthorGroupMemberRole.ADMIN.value


def _resolve_actor_group_role(
    db,
    *,
    group_id: UUID,
    author,
) -> str:
    if is_super_admin(author):
        return AuthorGroupMemberRole.OWNER.value
    member = _get_member_or_403(db=db, group_id=group_id, author_id=author.id)
    return _to_role_value(member.role)


def _assert_invite_role_allowed(*, actor_role: str, invite_role: str) -> None:
    if invite_role == AuthorGroupMemberRole.OWNER.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=OWNER_ROLE_NOT_ASSIGNABLE,
        )
    if invite_role == _ADMIN_INVITE_ROLE and actor_role != AuthorGroupMemberRole.OWNER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group owner can invite with ADMIN role",
        )


def _assert_role_not_owner_assignment(requested_role: str) -> None:
    if requested_role == AuthorGroupMemberRole.OWNER.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=OWNER_ROLE_NOT_ASSIGNABLE,
        )


def _assert_can_revoke_invite(*, actor_role: str, invite: AuthorGroupInvite) -> None:
    if _to_role_value(invite.role) == AuthorGroupMemberRole.ADMIN.value and actor_role != AuthorGroupMemberRole.OWNER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group owner can revoke an ADMIN invitation",
        )


def _assert_role_change_allowed(
    *,
    actor_role: str,
    actor_author_id: UUID,
    target_author_id: UUID,
    target_role: str,
    requested_role: str,
) -> None:
    _assert_role_not_owner_assignment(requested_role)
    if actor_role == AuthorGroupMemberRole.OWNER.value:
        return
    if target_role == AuthorGroupMemberRole.ADMIN.value and target_author_id != actor_author_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group owner can change an ADMIN member's role",
        )
    if requested_role == AuthorGroupMemberRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group owner can assign the ADMIN role",
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


def _series_to_dtos(db: Session, series_list: List[Series]) -> List[SeriesListItemDTO]:
    if not series_list:
        return []
    series_ids = [series.id for series in series_list]
    plan_count_map = get_active_plan_count_map_by_series_ids(db=db, series_ids=series_ids)
    return [
        _series_to_list_item_dto(series, plan_count=plan_count_map.get(series.id, 0))
        for series in series_list
    ]


def _language_value(language) -> str:
    if language is None:
        return "EN"
    if hasattr(language, "value"):
        return language.value
    return str(language)


def _plan_aggregate_to_dto(plan_info: PlanWithAggregates, group_id: UUID) -> PlanDTO:
    plan = plan_info.plan
    author_dto = None
    if plan.author:
        author_dto = AuthorDTO(
            id=plan.author_id,
            firstname=plan.author.first_name,
            lastname=plan.author.last_name,
            image_url=_generate_group_asset_url(plan.author.image_url),
            image_key=plan.author.image_url,
        )
    return PlanDTO(
        id=plan.id,
        title=plan.title,
        description=plan.description,
        language=_language_value(plan.language),
        difficulty_level=plan.difficulty_level,
        image_url=_generate_group_asset_url(plan.image_url),
        image_key=plan.image_url,
        total_days=int(plan_info.total_days or 0),
        tags=tags_to_summary_dtos(plan.tag_list),
        status=PlanStatus(plan.status.value),
        featured=bool(plan.featured),
        subscription_count=int(plan_info.subscription_count or 0),
        author=author_dto,
        start_date=plan.start_date,
        series_id=plan.series_id,
        display_order=plan.display_order,
        group_id=group_id,
    )


def _plans_to_dtos(db: Session, plan_list: List[Plan], group_id: UUID) -> List[PlanDTO]:
    if not plan_list:
        return []
    plan_ids = [plan.id for plan in plan_list]
    aggregate_by_id = {
        item.plan.id: item
        for item in get_plans_with_aggregates_by_ids(db=db, plan_ids=plan_ids)
    }
    return [
        _plan_aggregate_to_dto(aggregate_by_id[plan.id], group_id=group_id)
        for plan in plan_list
        if plan.id in aggregate_by_id
    ]


def _group_to_summary(
    group: AuthorGroup,
    follower_count: int = 0, public: bool = False,
    language: Optional[str] = None,
) -> AuthorGroupSummaryDTO:
    dto_class = PublicAuthorGroupSummaryDTO if public else AuthorGroupSummaryDTO
    tags = _group_tag_names(group.tags) if public else tags_to_summary_dtos(group.tags)
    return dto_class(
        id=group.id,
        slug=group.slug,
        is_public=group.is_public,
        avatar_key=group.avatar_key,
        banner_key=group.banner_key,
        avatar_url=_generate_group_asset_url(group.avatar_key),
        banner_url=_generate_group_asset_url(group.banner_key),
        metadata=_metadata_response(group.metadata_entries, language=language),
        tags=tags,
        follower_count=follower_count,
        member_count=len(group.members),
    )


def _group_to_detail(
    group: AuthorGroup,
    follower_count: int = 0,
    db: Optional[Session] = None,
    public: bool = False,
    language: Optional[str] = None,
) -> AuthorGroupDetailDTO:
    if db is not None:
        group_series = get_series_by_group_id(db=db, group_id=group.id)
        group_plans = get_plans_by_group_id(db=db, group_id=group.id)
        series_dtos = _series_to_dtos(db=db, series_list=group_series)
        plans_dtos = _plans_to_dtos(db=db, plan_list=group_plans, group_id=group.id)
    else:
        series_dtos = []
        plans_dtos = []

    dto_class = PublicAuthorGroupDetailDTO if public else AuthorGroupDetailDTO
    tags = _group_tag_names(group.tags) if public else tags_to_summary_dtos(group.tags)
    return dto_class(
        id=group.id,
        slug=group.slug,
        is_public=group.is_public,
        avatar_key=group.avatar_key,
        banner_key=group.banner_key,
        avatar_url=_generate_group_asset_url(group.avatar_key),
        banner_url=_generate_group_asset_url(group.banner_key),
        metadata=_metadata_response(group.metadata_entries, language=language),
        members=_members_to_dtos(group.members),
        tags=tags,
        social_links=_social_links_to_dtos(group.social_links),
        series=series_dtos,
        plans=plans_dtos,
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
                sub_title=item.sub_title,
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
        return _group_to_detail(loaded, follower_count=0, db=db)


def update_author_group(token: str, group_id: UUID, request: UpdateAuthorGroupRequest) -> AuthorGroupDetailDTO:
    author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
        if not is_super_admin(author):
            member = _get_member_or_403(db=db, group_id=group_id, author_id=author.id)
            _assert_role_allowed(member=member, allowed_roles=_GROUP_SETTINGS_ROLES)

        fields_set = request.model_fields_set

        if "slug" in fields_set:
            if request.slug != group.slug:
                existing = get_group_by_slug(db=db, slug=request.slug)
                if existing and existing.id != group.id:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group slug already exists")
            group.slug = request.slug
        if "is_public" in fields_set:
            group.is_public = request.is_public
        if "avatar_key" in fields_set:
            group.avatar_key = request.avatar_key
        if "banner_key" in fields_set:
            group.banner_key = request.banner_key
        if "metadata" in fields_set:
            _assert_metadata_valid(request.metadata)
            metadata_entries = [
                AuthorGroupMetadata(
                    language=item.language.value,
                    title=item.title,
                    sub_title=item.sub_title,
                    description=item.description,
                )
                for item in request.metadata
            ]
            replace_group_metadata(db=db, group_id=group_id, metadata_entries=metadata_entries)
            db.expire(group, ["metadata_entries"])

        group.updated_by = author.email
        group.updated_at = datetime.now(timezone.utc)
        update_group(db=db, group=group)
        loaded = get_group_by_id(db=db, group_id=group_id)
        followers_count = get_followers_count_map(db=db, group_ids=[group_id]).get(group_id, 0)
        return _group_to_detail(group=loaded, follower_count=followers_count, db=db)


def get_author_group_detail(group_id: UUID, require_public: bool = True) -> PublicAuthorGroupDetailDTO:
    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
        if require_public and not group.is_public:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
        follower_count = get_followers_count_map(db=db, group_ids=[group_id]).get(group_id, 0)
        return _group_to_detail(group=group, follower_count=follower_count, db=db, public=True)


def get_cms_group_detail(token: str, group_id: UUID) -> AuthorGroupDetailDTO:
    author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
        if not is_super_admin(author) and not is_reviewer(author):
            _get_member_or_403(db=db, group_id=group_id, author_id=author.id)
        follower_count = get_followers_count_map(db=db, group_ids=[group_id]).get(group_id, 0)
        return _group_to_detail(group=group, follower_count=follower_count, db=db)


def list_public_groups(
    skip: int,
    limit: int,
    search: Optional[str] = None,
    language: Optional[str] = None,
    tag_id: Optional[UUID] = None,
) -> PublicAuthorGroupListResponse:
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
        return PublicAuthorGroupListResponse(
            groups=[
                _group_to_summary(
                    group=item,
                    follower_count=follower_count_map.get(item.id, 0), public=True,
                    language=language,
                )
                for item in groups
            ],
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
    for_transfer: bool = False,
) -> AuthorGroupListResponse:
    author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        group_ids = None
        if for_transfer:
            require_cms_write_access(author)
        elif not is_super_admin(author) and not is_reviewer(author):
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
            groups=[
                _group_to_summary(
                    group=item,
                    follower_count=follower_count_map.get(item.id, 0),
                    language=language,
                )
                for item in groups
            ],
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
        if not is_super_admin(author):
            member = _get_member_or_403(db=db, group_id=group_id, author_id=author.id)
            _assert_role_allowed(member=member, allowed_roles=_GROUP_SETTINGS_ROLES)
        _validate_group_links(db=db, tag_ids=request.tag_ids, series_ids=None, plan_ids=None)
        replace_group_relation_ids(db=db, table=author_group_tags, group_id=group_id, column_name="tag_id", ids=request.tag_ids)
        db.commit()
        loaded = get_group_by_id(db=db, group_id=group_id)
        follower_count = get_followers_count_map(db=db, group_ids=[group_id]).get(group_id, 0)
        return _group_to_detail(loaded, follower_count=follower_count, db=db)


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
        if not is_super_admin(author):
            member = _get_member_or_403(db=db, group_id=group_id, author_id=author.id)
            _assert_role_allowed(member=member, allowed_roles=_GROUP_SETTINGS_ROLES)
        social_links = [AuthorGroupSocialLink(platform=item.platform, url=item.url) for item in request.social_links]
        replace_group_social_links(db=db, group_id=group_id, social_links=social_links)
        db.commit()
        loaded = get_group_by_id(db=db, group_id=group_id)
        follower_count = get_followers_count_map(db=db, group_ids=[group_id]).get(group_id, 0)
        return _group_to_detail(loaded, follower_count=follower_count, db=db)


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


def list_followed_groups(token: str, skip: int, limit: int) -> PublicAuthorGroupListResponse:
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
        return PublicAuthorGroupListResponse(
            groups=[_group_to_summary(group=item, follower_count=follower_count_map.get(item.id, 0), public=True) for item in groups],
            skip=skip,
            limit=limit,
            total=total,
        )


def _to_invite_status(status_value) -> AuthorGroupInviteStatus:
    if hasattr(status_value, "value"):
        return AuthorGroupInviteStatus(status_value.value)
    return AuthorGroupInviteStatus(status_value)


def _group_name_from_invite(invite: AuthorGroupInvite) -> str:
    group = getattr(invite, "group", None)
    if group is not None and group.metadata_entries:
        return _group_title_from_metadata(group.metadata_entries)
    return "Group"


def _invite_to_dto(
    invite: AuthorGroupInvite,
    *,
    group_name: Optional[str] = None,
    db: Optional[Session] = None,
) -> GroupInviteDTO:
    resolved_group_name = group_name if group_name is not None else _group_name_from_invite(invite)
    inviter_email = invite.created_by
    inviter_name = inviter_email
    if db is not None:
        inviter = get_author_by_email(db=db, email=inviter_email)
        if inviter:
            display_name = _inviter_display_name(inviter)
            if display_name:
                inviter_name = display_name
    return GroupInviteDTO(
        id=invite.id,
        group_id=invite.group_id,
        group_name=resolved_group_name,
        target_email=invite.target_email,
        role=AuthorGroupMemberRole(_to_role_value(invite.role)),
        status=_to_invite_status(invite.status),
        expires_at=invite.expires_at,
        accepted_at=invite.accepted_at,
        rejected_at=invite.rejected_at,
        revoked_at=invite.revoked_at,
        created_at=invite.created_at,
        created_by=invite.created_by,
        inviter_name=inviter_name,
        inviter_email=inviter_email,
    )


def _inviter_display_name(author) -> str:
    parts = [getattr(author, "first_name", None), getattr(author, "last_name", None)]
    name = " ".join(part for part in parts if isinstance(part, str) and part.strip()).strip()
    email = getattr(author, "email", None)
    if isinstance(email, str) and email.strip():
        return name or email
    return name


def _group_title_from_metadata(metadata_entries) -> str:
    if not metadata_entries:
        return "Group"
    for entry in metadata_entries:
        language = entry.language
        lang_value = language.value if hasattr(language, "value") else str(language)
        if lang_value.upper() == "EN":
            return entry.title
    return metadata_entries[0].title


def _invite_expires_at() -> datetime:
    """Invite TTL is minutes only (default 30), not days — see GROUP_INVITE_EXPIRY_MINUTES."""
    minutes = get_int("GROUP_INVITE_EXPIRY_MINUTES")
    minutes = max(1, min(minutes, 24 * 60))
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)


def _assert_invite_pending_for_recipient(invite: AuthorGroupInvite, author_email: str) -> None:
    if invite.target_email.lower() != author_email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation was sent to a different email address",
        )
    invite_status = _to_invite_status(invite.status)
    if invite_status != AuthorGroupInviteStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invite is not pending (status: {invite_status.value})",
        )
    if invite.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite has expired")


def _mark_invite_notification_read(db, *, recipient_author_id: UUID, invite_id: UUID) -> None:
    mark_notifications_read_by_reference(
        db=db,
        recipient_author_id=recipient_author_id,
        category=NOTIFICATION_CATEGORY_GROUP_INVITE,
        reference_id=invite_id,
    )


def create_group_member_invite(
    token: str,
    group_id: UUID,
    request: CreateGroupInviteRequest,
) -> GroupInviteCreatedResponse:
    author = validate_and_extract_author_details(token=token)
    target_email = request.target_email.strip().lower()
    if not target_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="target_email is required")

    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
        actor_role = _resolve_actor_group_role(db, group_id=group_id, author=author)
        if not is_super_admin(author):
            member = _get_member_or_403(db=db, group_id=group_id, author_id=author.id)
            _assert_role_allowed(member=member, allowed_roles=_MEMBER_MANAGEMENT_ROLES)

        _assert_invite_role_allowed(
            actor_role=actor_role,
            invite_role=_to_role_value(request.role),
        )

        target_author = get_author_by_email(db=db, email=target_email)
        if not target_author:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No registered author exists with this email address",
            )
        if get_group_member(db=db, group_id=group_id, author_id=target_author.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This author is already a member of this group",
            )
        if has_pending_invite(db=db, group_id=group_id, target_email=target_email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A pending invitation already exists for this email",
            )

        invite = AuthorGroupInvite(
            group_id=group_id,
            target_email=target_email,
            role=request.role,
            status=AuthorGroupInviteStatus.PENDING.value,
            expires_at=_invite_expires_at(),
            created_by=author.email,
        )
        created = create_group_invite(db=db, invite=invite)
        loaded_group = get_group_by_id(db=db, group_id=group_id)
        group_title = _group_title_from_metadata(loaded_group.metadata_entries)
        inviter_name = _inviter_display_name(author)
        target_author_id = target_author.id
        created_invite_id = created.id
        invite_dto = _invite_to_dto(created, group_name=group_title, db=db)

    notification = create_notification_record(
        recipient_author_id=target_author_id,
        title=f"Invitation to join {group_title}",
        description=f"{inviter_name} invited you to join {group_title}.",
        category=NOTIFICATION_CATEGORY_GROUP_INVITE,
        reference_id=created_invite_id,
    )

    send_group_invitation_email(
        target_email=target_email,
        inviter_name=inviter_name,
        inviter_email=author.email,
        group_title=group_title,
        invite_role=_to_role_value(request.role),
    )

    return GroupInviteCreatedResponse(
        invite=invite_dto,
        notification_id=notification.id,
    )


def list_group_invites(
    token: str,
    group_id: UUID,
    status_filter: Optional[AuthorGroupInviteStatus] = None,
) -> GroupInviteListResponse:
    author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
        if not is_super_admin(author):
            member = _get_member_or_403(db=db, group_id=group_id, author_id=author.id)
            _assert_role_allowed(member=member, allowed_roles=[AuthorGroupMemberRole.OWNER, AuthorGroupMemberRole.ADMIN])

        rows = list_invites_by_group(db=db, group_id=group_id, status=status_filter)
        invite_dtos = [_invite_to_dto(row, db=db) for row in rows]
    return GroupInviteListResponse(
        invites=invite_dtos,
        total=len(invite_dtos),
    )


def list_my_pending_group_invites(token: str) -> GroupInviteListResponse:
    author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        rows = list_pending_invites_by_email(db=db, target_email=author.email)
        invite_dtos = [_invite_to_dto(row, db=db) for row in rows]
    return GroupInviteListResponse(
        invites=invite_dtos,
        total=len(invite_dtos),
    )


def accept_group_invite_by_id(token: str, invite_id: UUID) -> AuthorGroupDetailDTO:
    author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        invite = get_invite_by_id(db=db, invite_id=invite_id, load_group=True)
        if not invite:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=INVITE_NOT_FOUND)
        _assert_invite_pending_for_recipient(invite=invite, author_email=author.email)

        group = get_group_by_id(db=db, group_id=invite.group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)

        invite_role = _to_role_value(invite.role)
        if invite_role == AuthorGroupMemberRole.OWNER.value and get_owner_count(db=db, group_id=group.id) >= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=GROUP_ALREADY_HAS_OWNER,
            )
        _assert_role_not_owner_assignment(invite_role)

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

        now = datetime.now(timezone.utc)
        invite.status = AuthorGroupInviteStatus.ACCEPTED.value
        invite.accepted_at = now
        save_invite(db=db, invite=invite)
        _mark_invite_notification_read(db=db, recipient_author_id=author.id, invite_id=invite.id)

        loaded = get_group_by_id(db=db, group_id=group.id)
        follower_count = get_followers_count_map(db=db, group_ids=[group.id]).get(group.id, 0)
        return _group_to_detail(loaded, follower_count=follower_count, db=db)


def reject_group_invite_by_id(token: str, invite_id: UUID) -> GroupInviteDTO:
    author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        invite = get_invite_by_id(db=db, invite_id=invite_id)
        if not invite:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=INVITE_NOT_FOUND)
        _assert_invite_pending_for_recipient(invite=invite, author_email=author.email)

        invite.status = AuthorGroupInviteStatus.REJECTED.value
        invite.rejected_at = datetime.now(timezone.utc)
        save_invite(db=db, invite=invite)
        _mark_invite_notification_read(db=db, recipient_author_id=author.id, invite_id=invite.id)
        return _invite_to_dto(invite, db=db)


def revoke_group_invite(token: str, group_id: UUID, invite_id: UUID) -> None:
    author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
        actor_role = _resolve_actor_group_role(db, group_id=group_id, author=author)
        if not is_super_admin(author):
            member = _get_member_or_403(db=db, group_id=group_id, author_id=author.id)
            _assert_role_allowed(member=member, allowed_roles=_MEMBER_MANAGEMENT_ROLES)

        invite = get_invite_by_id(db=db, invite_id=invite_id)
        if not invite or invite.group_id != group_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=INVITE_NOT_FOUND)
        _assert_can_revoke_invite(actor_role=actor_role, invite=invite)
        if _to_invite_status(invite.status) != AuthorGroupInviteStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending invites can be revoked",
            )
        revoke_invite(db=db, invite=invite, revoked_by=author.email)
        target_author = get_author_by_email(db=db, email=invite.target_email)
        if target_author:
            _mark_invite_notification_read(
                db=db,
                recipient_author_id=target_author.id,
                invite_id=invite.id,
            )


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
        if not is_super_admin(current_author):
            current_member = _get_member_or_403(db=db, group_id=group_id, author_id=current_author.id)
            _assert_role_allowed(current_member, [AuthorGroupMemberRole.OWNER, AuthorGroupMemberRole.ADMIN])

        target_member = get_group_member(db=db, group_id=group_id, author_id=author_id)
        if not target_member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group member not found")

        target_role = _to_role_value(target_member.role)
        requested_role = _to_role_value(request.role)
        actor_role = _resolve_actor_group_role(db, group_id=group_id, author=current_author)
        if target_role == AuthorGroupMemberRole.OWNER.value and actor_role != AuthorGroupMemberRole.OWNER.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change the role of a group owner",
            )
        _assert_role_change_allowed(
            actor_role=actor_role,
            actor_author_id=current_author.id,
            target_author_id=author_id,
            target_role=target_role,
            requested_role=requested_role,
        )

        if target_role == AuthorGroupMemberRole.OWNER.value and requested_role != AuthorGroupMemberRole.OWNER.value:
            owner_count = get_owner_count(db=db, group_id=group_id)
            if owner_count <= 1:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one OWNER must always remain")

        set_group_member_role(db=db, member=target_member, role=request.role.value, updated_by=current_author.email)
        loaded = get_group_by_id(db=db, group_id=group_id)
        follower_count = get_followers_count_map(db=db, group_ids=[group_id]).get(group_id, 0)
        return _group_to_detail(loaded, follower_count=follower_count, db=db)


def _assert_not_last_owner_removal(db, *, group_id: UUID, member: AuthorGroupMember) -> None:
    if _to_role_value(member.role) != "OWNER":
        return
    owner_count = get_owner_count(db=db, group_id=group_id)
    if owner_count <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one OWNER must remain. Transfer ownership or delete the group.",
        )


def _assert_admin_can_remove_target(
    current_member: AuthorGroupMember,
    target_member: AuthorGroupMember,
) -> None:
    current_role = _to_role_value(current_member.role)
    target_role = _to_role_value(target_member.role)
    if current_role == AuthorGroupMemberRole.ADMIN.value and target_role in (
        AuthorGroupMemberRole.OWNER.value,
        AuthorGroupMemberRole.ADMIN.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group owner can remove a member with role OWNER or ADMIN",
        )
def transfer_group_ownership(
    token: str,
    group_id: UUID,
    new_owner_author_id: UUID,
) -> AuthorGroupDetailDTO:
    current_author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)

        current_member = get_group_member(db=db, group_id=group_id, author_id=current_author.id)
        if not current_member or _to_role_value(current_member.role) != AuthorGroupMemberRole.OWNER.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the group owner can transfer ownership",
            )

        if new_owner_author_id == current_author.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already the group owner",
            )

        new_owner_member = get_group_member(db=db, group_id=group_id, author_id=new_owner_author_id)
        if not new_owner_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group member not found",
            )
        if _to_role_value(new_owner_member.role) == AuthorGroupMemberRole.OWNER.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected member is already the group owner",
            )

        set_group_member_role(
            db=db,
            member=current_member,
            role=AuthorGroupMemberRole.ADMIN.value,
            updated_by=current_author.email,
        )
        set_group_member_role(
            db=db,
            member=new_owner_member,
            role=AuthorGroupMemberRole.OWNER.value,
            updated_by=current_author.email,
        )

        loaded = get_group_by_id(db=db, group_id=group_id)
        follower_count = get_followers_count_map(db=db, group_ids=[group_id]).get(group_id, 0)
        return _group_to_detail(loaded, follower_count=follower_count, db=db)


def delete_group_member(token: str, group_id: UUID, author_id: UUID) -> None:
    current_author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)

        is_self_remove = author_id == current_author.id
        member = get_group_member(db=db, group_id=group_id, author_id=author_id)
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group member not found")

        if is_self_remove:
            if not is_super_admin(current_author):
                _get_member_or_403(db=db, group_id=group_id, author_id=current_author.id)
            _assert_not_last_owner_removal(db, group_id=group_id, member=member)
        else:
            if not is_super_admin(current_author):
                current_member = _get_member_or_403(db=db, group_id=group_id, author_id=current_author.id)
                _assert_role_allowed(
                    current_member,
                    [AuthorGroupMemberRole.OWNER, AuthorGroupMemberRole.ADMIN],
                )
                _assert_admin_can_remove_target(current_member, member)
            _assert_not_last_owner_removal(db, group_id=group_id, member=member)

        remove_group_member(db=db, member=member)
