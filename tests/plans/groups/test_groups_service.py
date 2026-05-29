import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from starlette import status

from pecha_api.plans.groups.groups_enums import AuthorGroupMemberRole
from pecha_api.plans.groups.groups_response_models import (
    AcceptGroupInviteRequest,
    CreateAuthorGroupRequest,
    CreateGroupInviteRequest,
    GroupMetadataInput,
    GroupSocialLinkInput,
    ReplaceGroupPlansRequest,
    ReplaceGroupSeriesRequest,
    ReplaceGroupSocialLinksRequest,
    ReplaceGroupTagsRequest,
    UpdateAuthorGroupRequest,
    UpdateGroupMemberRoleRequest,
)
from pecha_api.plans.groups.groups_service import (
    GROUP_NOT_FOUND,
    InviteEmailMismatchError,
    _assert_metadata_valid,
    _generate_group_asset_url,
    _get_member_or_403,
    _group_to_detail,
    _to_role_value,
    accept_group_invite,
    create_author_group,
    create_group_member_invite,
    delete_group_member,
    follow_group,
    get_author_group_detail,
    get_cms_group_detail,
    list_cms_groups,
    list_followed_groups,
    list_public_groups,
    replace_group_plans_by_id,
    replace_group_series_by_id,
    replace_group_social_links_by_id,
    replace_group_tags,
    revoke_group_invite,
    unfollow_group,
    update_author_group,
    update_group_member_role,
)
from pecha_api.plans.plans_enums import LanguageCode


def _session_local_context(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_session_local.return_value.__exit__.return_value = False
    return mock_db


def _make_author(author_id=None, email="author@example.org", is_admin=False):
    author = MagicMock()
    author.id = author_id or uuid4()
    author.email = email
    author.is_admin = is_admin
    return author


def _make_group(is_public=True, slug="test-group"):
    group = MagicMock()
    group.id = uuid4()
    group.slug = slug
    group.is_public = is_public
    group.avatar_key = None
    group.banner_key = None
    group.metadata_entries = []
    group.members = []
    group.social_links = []
    group.tags = []
    group.plans = []
    group.series = []
    return group


def _metadata_input(title="Title", language=LanguageCode.EN):
    return GroupMetadataInput(title=title, description="Desc", language=language)


def test_generate_group_asset_url_returns_none_for_empty_key():
    assert _generate_group_asset_url(None) is None
    assert _generate_group_asset_url("") is None


def test_group_to_detail_includes_presigned_avatar_and_banner_urls():
    group = _make_group()
    group.avatar_key = "images/avatar.jpg"
    group.banner_key = "images/banner.jpg"
    with patch(
        "pecha_api.plans.groups.groups_service.generate_presigned_access_url",
        side_effect=lambda bucket_name, s3_key: f"https://signed.example/{s3_key}",
    ):
        detail = _group_to_detail(group)
    assert detail.avatar_key == "images/avatar.jpg"
    assert detail.banner_key == "images/banner.jpg"
    assert detail.avatar_url == "https://signed.example/images/avatar.jpg"
    assert detail.banner_url == "https://signed.example/images/banner.jpg"


def test_assert_metadata_valid_rejects_empty():
    with pytest.raises(HTTPException) as exc:
        _assert_metadata_valid([])
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST


def test_assert_metadata_valid_rejects_duplicate_language():
    with pytest.raises(HTTPException) as exc:
        _assert_metadata_valid(
            [
                _metadata_input(language=LanguageCode.EN),
                _metadata_input(title="Other", language=LanguageCode.EN),
            ]
        )
    assert "unique" in exc.value.detail.lower()


def test_assert_metadata_valid_rejects_missing_title():
    entry = _metadata_input()
    entry.title = ""
    with pytest.raises(HTTPException) as exc:
        _assert_metadata_valid([entry])
    assert "title" in exc.value.detail.lower()


def test_to_role_value_accepts_string():
    assert _to_role_value("OWNER") == "OWNER"


def test_get_member_or_403_raises_when_not_member():
    with patch("pecha_api.plans.groups.groups_service.get_group_member", return_value=None):
        with pytest.raises(HTTPException) as exc:
            _get_member_or_403(db=MagicMock(), group_id=uuid4(), author_id=uuid4())
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_get_cms_group_detail_success():
    author = _make_author(is_admin=True)
    group = _make_group()
    meta = MagicMock()
    meta.id = uuid4()
    meta.title = "T"
    meta.description = "D"
    meta.language = "EN"
    group.metadata_entries = [meta]

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={group.id: 2},
    ):
        _session_local_context(mock_session)
        result = get_cms_group_detail(token="t", group_id=group.id)
    assert result.follower_count == 2


def test_update_author_group_success_as_admin():
    author = _make_author(is_admin=True)
    group = _make_group()
    meta = MagicMock()
    meta.id = uuid4()
    meta.title = "T"
    meta.description = "D"
    meta.language = "EN"
    group.metadata_entries = [meta]

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.update_group",
    ), patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={group.id: 0},
    ):
        _session_local_context(mock_session)
        result = update_author_group(
            token="t",
            group_id=group.id,
            request=UpdateAuthorGroupRequest(is_public=False),
        )
    assert result.is_public is False


def test_accept_group_invite_revoked():
    author = _make_author(email="a@b.com")
    invite = MagicMock()
    invite.target_email = "a@b.com"
    invite.revoked_at = datetime.now(timezone.utc)
    invite.expires_at = datetime.now(timezone.utc) + timedelta(days=1)
    invite.max_uses = 1
    invite.uses_count = 0

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_invite_by_token_hash",
        return_value=invite,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            accept_group_invite(token="t", request=AcceptGroupInviteRequest(token="raw"))
    assert "revoked" in exc.value.detail.lower()


def test_accept_group_invite_not_found():
    author = _make_author()
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_invite_by_token_hash",
        return_value=None,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            accept_group_invite(token="t", request=AcceptGroupInviteRequest(token="raw"))
    assert exc.value.detail == "Invite not found"


def test_replace_group_series_invalid_ids():
    author = _make_author()
    group = _make_group()
    series_id = uuid4()
    current = MagicMock()
    current.role = AuthorGroupMemberRole.OWNER

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        return_value=current,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_series_by_ids",
        return_value=[],
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            replace_group_series_by_id(
                token="t",
                group_id=group.id,
                request=ReplaceGroupSeriesRequest(series_ids=[series_id]),
            )
    assert "series" in exc.value.detail.lower()


def test_create_author_group_success():
    author = _make_author()
    request = CreateAuthorGroupRequest(
        slug="new-group",
        is_public=True,
        metadata=[_metadata_input()],
    )
    created = _make_group(slug="new-group")
    created.id = uuid4()
    meta = MagicMock()
    meta.id = uuid4()
    meta.title = "Title"
    meta.description = "Desc"
    meta.language = "EN"
    created.metadata_entries = [meta]

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_slug",
        return_value=None,
    ), patch(
        "pecha_api.plans.groups.groups_service.create_group",
        return_value=created,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=created,
    ):
        _session_local_context(mock_session)
        result = create_author_group(token="t", request=request)

    assert result.slug == "new-group"


def test_create_author_group_slug_exists():
    author = _make_author()
    request = CreateAuthorGroupRequest(slug="taken", metadata=[_metadata_input()])

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_slug",
        return_value=_make_group(slug="taken"),
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            create_author_group(token="t", request=request)
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST


def test_get_author_group_detail_not_found():
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=None,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            get_author_group_detail(group_id=uuid4())
    assert exc.value.detail == GROUP_NOT_FOUND


def test_get_author_group_detail_private_group_hidden():
    private_group = _make_group(is_public=False)
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=private_group,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            get_author_group_detail(group_id=private_group.id, require_public=True)
    assert exc.value.detail == GROUP_NOT_FOUND


def test_list_public_groups_returns_paginated():
    group = _make_group()
    meta = MagicMock()
    meta.id = uuid4()
    meta.title = "T"
    meta.description = None
    meta.language = "EN"
    group.metadata_entries = [meta]
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.get_groups_paginated",
        return_value=([group], 1),
    ), patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={group.id: 3},
    ):
        _session_local_context(mock_session)
        result = list_public_groups(skip=0, limit=10)

    assert result.total == 1
    assert result.groups[0].follower_count == 3


def test_list_cms_groups_scopes_to_member_groups_for_non_admin():
    author = _make_author(is_admin=False)
    group = _make_group()
    membership = MagicMock()
    membership.group_id = group.id

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [membership]

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_groups_paginated",
        return_value=([group], 1),
    ) as mock_paginated, patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={},
    ):
        mock_session.return_value.__enter__.return_value = mock_db
        mock_session.return_value.__exit__.return_value = False
        list_cms_groups(token="t", skip=0, limit=10)

    assert mock_paginated.call_args.kwargs["group_ids"] == [group.id]


def test_follow_group_requires_public_group():
    user = MagicMock()
    user.id = uuid4()
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_user_details",
        return_value=user,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=None,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            follow_group(token="t", group_id=uuid4())
    assert exc.value.detail == GROUP_NOT_FOUND


def test_follow_group_success():
    user = MagicMock()
    user.id = uuid4()
    group = _make_group(is_public=True)

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_user_details",
        return_value=user,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.upsert_group_follow",
    ) as mock_follow:
        _session_local_context(mock_session)
        follow_group(token="t", group_id=group.id)
    mock_follow.assert_called_once()


def test_unfollow_group_calls_repository():
    user = MagicMock()
    user.id = uuid4()
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_user_details",
        return_value=user,
    ), patch(
        "pecha_api.plans.groups.groups_service.remove_group_follow",
    ) as mock_unfollow:
        _session_local_context(mock_session)
        unfollow_group(token="t", group_id=uuid4())
    mock_unfollow.assert_called_once()


def test_list_followed_groups():
    user = MagicMock()
    user.id = uuid4()
    group = _make_group()
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_user_details",
        return_value=user,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_following_group_ids_by_user",
        return_value=[group.id],
    ), patch(
        "pecha_api.plans.groups.groups_service.get_groups_paginated",
        return_value=([group], 1),
    ), patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={},
    ):
        _session_local_context(mock_session)
        result = list_followed_groups(token="t", skip=0, limit=20)
    assert result.total == 1


def test_create_group_member_invite_returns_raw_token():
    author = _make_author()
    group = _make_group()
    invite = MagicMock()
    invite.id = uuid4()
    invite.target_email = "invitee@example.org"
    invite.role = AuthorGroupMemberRole.AUTHOR
    invite.expires_at = datetime.now(timezone.utc) + timedelta(days=1)
    invite.max_uses = 1

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        return_value=MagicMock(role=AuthorGroupMemberRole.OWNER),
    ), patch(
        "pecha_api.plans.groups.groups_service.create_group_invite",
        return_value=invite,
    ):
        _session_local_context(mock_session)
        result = create_group_member_invite(
            token="t",
            group_id=group.id,
            request=CreateGroupInviteRequest(
                target_email="invitee@example.org",
                role=AuthorGroupMemberRole.AUTHOR,
                expires_at=invite.expires_at,
                max_uses=1,
            ),
        )
    assert result.token
    assert result.target_email == "invitee@example.org"


def test_accept_group_invite_email_mismatch():
    author = _make_author(email="other@example.org")
    invite = MagicMock()
    invite.target_email = "invitee@example.org"
    invite.revoked_at = None
    invite.expires_at = datetime.now(timezone.utc) + timedelta(days=1)
    invite.max_uses = 1
    invite.uses_count = 0
    invite.group_id = uuid4()

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_invite_by_token_hash",
        return_value=invite,
    ):
        _session_local_context(mock_session)
        with pytest.raises(InviteEmailMismatchError):
            accept_group_invite(
                token="t",
                request=AcceptGroupInviteRequest(token="raw"),
            )


def test_accept_group_invite_expired():
    author = _make_author(email="invitee@example.org")
    invite = MagicMock()
    invite.target_email = "invitee@example.org"
    invite.revoked_at = None
    invite.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    invite.max_uses = 1
    invite.uses_count = 0

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_invite_by_token_hash",
        return_value=invite,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            accept_group_invite(token="t", request=AcceptGroupInviteRequest(token="raw"))
    assert "expired" in exc.value.detail.lower()


def test_accept_group_invite_success_adds_member():
    author = _make_author(email="invitee@example.org")
    group = _make_group()
    invite = MagicMock()
    invite.target_email = "invitee@example.org"
    invite.revoked_at = None
    invite.expires_at = datetime.now(timezone.utc) + timedelta(days=1)
    invite.max_uses = 1
    invite.uses_count = 0
    invite.role = AuthorGroupMemberRole.AUTHOR
    invite.group_id = group.id

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_invite_by_token_hash",
        return_value=invite,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        return_value=None,
    ), patch(
        "pecha_api.plans.groups.groups_service.add_group_member",
    ) as mock_add, patch(
        "pecha_api.plans.groups.groups_service.increase_invite_use_count",
    ), patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={},
    ):
        _session_local_context(mock_session)
        accept_group_invite(token="t", request=AcceptGroupInviteRequest(token="raw-token"))
    mock_add.assert_called_once()


def test_update_group_member_role_blocks_last_owner_demotion():
    author = _make_author()
    group = _make_group()
    target = MagicMock()
    target.role = AuthorGroupMemberRole.OWNER
    current = MagicMock()
    current.role = AuthorGroupMemberRole.ADMIN

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        side_effect=[current, target],
    ), patch(
        "pecha_api.plans.groups.groups_service.get_owner_count",
        return_value=1,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            update_group_member_role(
                token="t",
                group_id=group.id,
                author_id=uuid4(),
                request=UpdateGroupMemberRoleRequest(role=AuthorGroupMemberRole.ADMIN),
            )
    assert "OWNER" in exc.value.detail


def test_delete_group_member_blocks_last_owner_removal():
    author = _make_author()
    group = _make_group()
    member = MagicMock()
    member.role = AuthorGroupMemberRole.OWNER
    current = MagicMock()
    current.role = AuthorGroupMemberRole.ADMIN

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        side_effect=[current, member],
    ), patch(
        "pecha_api.plans.groups.groups_service.get_owner_count",
        return_value=1,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            delete_group_member(token="t", group_id=group.id, author_id=uuid4())
    assert "last owner" in exc.value.detail.lower()


def test_replace_group_tags_invalid_tag_ids():
    author = _make_author()
    group = _make_group()
    tag_id = uuid4()
    current = MagicMock()
    current.role = AuthorGroupMemberRole.OWNER

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        return_value=current,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_tags_by_ids",
        return_value=[],
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            replace_group_tags(
                token="t",
                group_id=group.id,
                request=ReplaceGroupTagsRequest(tag_ids=[tag_id]),
            )
    assert "tags" in exc.value.detail.lower()


def test_update_author_group_forbidden_for_viewer():
    author = _make_author()
    group = _make_group()
    viewer = MagicMock()
    viewer.role = AuthorGroupMemberRole.VIEWER

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        return_value=viewer,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            update_author_group(
                token="t",
                group_id=group.id,
                request=UpdateAuthorGroupRequest(slug="updated"),
            )
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_revoke_group_invite_not_found():
    author = _make_author()
    group = _make_group()
    current = MagicMock()
    current.role = AuthorGroupMemberRole.ADMIN

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        return_value=current,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_invite_by_id",
        return_value=None,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            revoke_group_invite(token="t", group_id=group.id, invite_id=uuid4())
    assert exc.value.detail == "Invite not found"


def test_accept_group_invite_uses_token_hash():
    raw = "secret-token"
    expected_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    author = _make_author(email="a@b.com")
    invite = MagicMock()
    invite.target_email = "a@b.com"
    invite.revoked_at = None
    invite.expires_at = datetime.now(timezone.utc) + timedelta(days=1)
    invite.max_uses = 1
    invite.uses_count = 0
    invite.role = AuthorGroupMemberRole.AUTHOR
    invite.group_id = uuid4()

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_invite_by_token_hash",
        return_value=invite,
    ) as mock_lookup, patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=_make_group(),
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        return_value=MagicMock(),
    ), patch(
        "pecha_api.plans.groups.groups_service.increase_invite_use_count",
    ), patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={},
    ):
        _session_local_context(mock_session)
        accept_group_invite(token="t", request=AcceptGroupInviteRequest(token=raw))
    mock_lookup.assert_called_once_with(db=mock_session.return_value.__enter__.return_value, token_hash=expected_hash)


def test_replace_group_plans_and_series_delegate_to_repository():
    author = _make_author()
    group = _make_group()
    plan_id = uuid4()
    series_id = uuid4()
    current = MagicMock()
    current.role = AuthorGroupMemberRole.EDITOR
    loaded = _make_group()

    base_patches = {
        "validate_and_extract_author_details": author,
        "get_group_by_id": group,
        "get_group_member": current,
        "get_plans_by_ids": [MagicMock(id=plan_id)],
        "get_series_by_ids": [MagicMock(id=series_id)],
        "get_followers_count_map": {},
    }

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        side_effect=[group, loaded],
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        return_value=current,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_plans_by_ids",
        return_value=[MagicMock(id=plan_id)],
    ), patch(
        "pecha_api.plans.groups.groups_service.replace_group_relation_ids",
    ) as mock_replace, patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={},
    ):
        db = _session_local_context(mock_session)
        replace_group_plans_by_id(
            token="t",
            group_id=group.id,
            request=ReplaceGroupPlansRequest(plan_ids=[plan_id]),
        )
        db.commit.assert_called()
        mock_replace.assert_called_once()

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        side_effect=[group, loaded],
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        return_value=current,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_series_by_ids",
        return_value=[MagicMock(id=series_id)],
    ), patch(
        "pecha_api.plans.groups.groups_service.replace_group_relation_ids",
    ), patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={},
    ):
        _session_local_context(mock_session)
        replace_group_series_by_id(
            token="t",
            group_id=group.id,
            request=ReplaceGroupSeriesRequest(series_ids=[series_id]),
        )

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        side_effect=[group, loaded],
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        return_value=current,
    ), patch(
        "pecha_api.plans.groups.groups_service.replace_group_social_links",
    ) as mock_links, patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={},
    ):
        _session_local_context(mock_session)
        replace_group_social_links_by_id(
            token="t",
            group_id=group.id,
            request=ReplaceGroupSocialLinksRequest(
                social_links=[GroupSocialLinkInput(platform="twitter", url="https://x.com/g")]
            ),
        )
    mock_links.assert_called_once()
