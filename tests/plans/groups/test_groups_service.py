from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from starlette import status

from pecha_api.plans.groups.groups_enums import AuthorGroupInviteStatus, AuthorGroupMemberRole, AuthorGroupType
from pecha_api.plans.groups.groups_response_models import (
    CreateAuthorGroupRequest,
    CreateGroupInviteRequest,
    GroupMetadataInput,
    GroupSeriesListItemDTO,
    GroupSocialLinkInput,
    ReplaceGroupSocialLinksRequest,
    ReplaceGroupTagsRequest,
    UpdateAuthorGroupRequest,
    UpdateGroupMemberRoleRequest,
)
from pecha_api.plans.groups.groups_service import (
    GROUP_NOT_FOUND,
    _assert_metadata_valid,
    _generate_group_asset_url,
    _get_member_or_403,
    _group_to_detail,
    _is_series_enrolled_for_group_context,
    _series_to_dtos,
    _to_role_value,
    accept_group_invite_by_id,
    create_author_group,
    create_group_member_invite,
    delete_group_member,
    list_group_invites,
    list_my_pending_group_invites,
    reject_group_invite_by_id,
    follow_group,
    get_followed_group,
    get_joined_group,
    get_author_group_detail,
    get_cms_group_detail,
    list_cms_groups,
    list_group_members,
    list_followed_groups,
    list_joined_groups,
    list_public_groups,
    replace_group_social_links_by_id,
    replace_group_tags,
    revoke_group_invite,
    join_group,
    leave_group,
    unfollow_group,
    update_author_group,
    transfer_group_ownership,
    update_group_member_role,
    OWNER_ROLE_NOT_ASSIGNABLE,
)
from pecha_api.plans.platform_enums import PlatformRole
from pecha_api.plans.plans_enums import LanguageCode


def _session_local_context(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_session_local.return_value.__exit__.return_value = False
    return mock_db


def _make_author(
    author_id=None,
    email="author@example.org",
    *,
    platform_role: PlatformRole = PlatformRole.CREATOR,
    is_admin: bool = False,
):
    author = MagicMock()
    author.id = author_id or uuid4()
    author.email = email
    author.platform_role = PlatformRole.SUPER_ADMIN if is_admin else platform_role
    author.first_name = None
    author.last_name = None
    author.is_active = True
    return author


def _make_group(is_public=True, slug="test-group", group_type=AuthorGroupType.PAGE):
    group = MagicMock()
    group.id = uuid4()
    group.slug = slug
    group.group_type = group_type
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


def test_accept_group_invite_not_pending():
    author = _make_author(email="a@b.com")
    invite = MagicMock()
    invite.target_email = "a@b.com"
    invite.status = AuthorGroupInviteStatus.REVOKED.value
    invite.expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_invite_by_id",
        return_value=invite,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            accept_group_invite_by_id(token="t", invite_id=uuid4())
    assert "not pending" in exc.value.detail.lower()


def test_accept_group_invite_not_found():
    author = _make_author()
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_invite_by_id",
        return_value=None,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            accept_group_invite_by_id(token="t", invite_id=uuid4())
    assert exc.value.detail == "Invite not found"


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


def test_list_group_members_not_found():
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=None,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            list_group_members(group_id=uuid4(), skip=0, limit=20)
    assert exc.value.detail == GROUP_NOT_FOUND


def test_list_group_members_returns_paginated_profiles():
    group = _make_group()
    user = MagicMock()
    user.username = "alice"
    user.firstname = "Alice"
    user.lastname = "Smith"
    user.avatar_url = "images/profile_images/alice.webp"
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.list_group_joiners_paginated",
        return_value=([user], 1),
    ), patch(
        "pecha_api.plans.groups.groups_service._user_avatar_url",
        return_value="https://example.com/avatar.webp",
    ):
        _session_local_context(mock_session)
        result = list_group_members(group_id=group.id, skip=0, limit=20)

    assert result.total_members == 1
    assert result.skip == 0
    assert result.limit == 20
    assert len(result.list) == 1
    assert result.list[0].username == "alice"
    assert result.list[0].fullname == "Alice Smith"
    assert result.list[0].avatar_url == "https://example.com/avatar.webp"


def test_list_public_groups_defaults_to_community_type():
    group = _make_group(group_type=AuthorGroupType.COMMUNITY)
    group.metadata_entries = []
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.get_groups_paginated",
        return_value=([group], 1),
    ) as mock_paginated, patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={},
    ), patch(
        "pecha_api.plans.groups.groups_service.get_joiners_count_map",
        return_value={},
    ):
        _session_local_context(mock_session)
        list_public_groups(skip=0, limit=10)

    assert mock_paginated.call_args.kwargs["group_type"] == AuthorGroupType.COMMUNITY


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
    ) as mock_paginated, patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={group.id: 3},
    ), patch(
        "pecha_api.plans.groups.groups_service.get_joiners_count_map",
        return_value={group.id: 2},
    ):
        _session_local_context(mock_session)
        result = list_public_groups(skip=0, limit=10, group_type=AuthorGroupType.COMMUNITY)

    assert result.total == 1
    assert result.groups[0].follower_count == 3
    assert result.groups[0].joiner_count == 2
    assert result.groups[0].group_type == AuthorGroupType.PAGE
    assert mock_paginated.call_args.kwargs["group_type"] == AuthorGroupType.COMMUNITY


def test_list_public_groups_without_token_does_not_exclude_joined_groups():
    group = _make_group(group_type=AuthorGroupType.COMMUNITY)
    group.metadata_entries = []
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.get_groups_paginated",
        return_value=([group], 1),
    ) as mock_paginated, patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={},
    ), patch(
        "pecha_api.plans.groups.groups_service.get_joiners_count_map",
        return_value={},
    ):
        _session_local_context(mock_session)
        list_public_groups(skip=0, limit=10)

    assert mock_paginated.call_args.kwargs["exclude_group_ids"] is None


def test_list_public_groups_with_token_excludes_joined_groups():
    group = _make_group(group_type=AuthorGroupType.COMMUNITY)
    group.metadata_entries = []
    user_id = uuid4()
    joined_group_id = uuid4()
    user = MagicMock()
    user.id = user_id
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_user_details",
        return_value=user,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_joined_group_ids_by_user",
        return_value=[joined_group_id],
    ), patch(
        "pecha_api.plans.groups.groups_service.get_groups_paginated",
        return_value=([group], 1),
    ) as mock_paginated, patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={},
    ), patch(
        "pecha_api.plans.groups.groups_service.get_joiners_count_map",
        return_value={},
    ):
        _session_local_context(mock_session)
        list_public_groups(skip=0, limit=10, token="valid-token")

    assert mock_paginated.call_args.kwargs["exclude_group_ids"] == [joined_group_id]


def test_list_public_groups_with_token_and_no_joined_groups_does_not_exclude():
    group = _make_group(group_type=AuthorGroupType.COMMUNITY)
    group.metadata_entries = []
    user = MagicMock()
    user.id = uuid4()
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_user_details",
        return_value=user,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_joined_group_ids_by_user",
        return_value=[],
    ), patch(
        "pecha_api.plans.groups.groups_service.get_groups_paginated",
        return_value=([group], 1),
    ) as mock_paginated, patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={},
    ), patch(
        "pecha_api.plans.groups.groups_service.get_joiners_count_map",
        return_value={},
    ):
        _session_local_context(mock_session)
        list_public_groups(skip=0, limit=10, token="valid-token")

    assert mock_paginated.call_args.kwargs["exclude_group_ids"] is None


def test_list_public_groups_with_invalid_token_does_not_exclude_joined_groups():
    group = _make_group(group_type=AuthorGroupType.COMMUNITY)
    group.metadata_entries = []
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_user_details",
        side_effect=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"),
    ), patch(
        "pecha_api.plans.groups.groups_service.get_groups_paginated",
        return_value=([group], 1),
    ) as mock_paginated, patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={},
    ), patch(
        "pecha_api.plans.groups.groups_service.get_joiners_count_map",
        return_value={},
    ):
        _session_local_context(mock_session)
        list_public_groups(skip=0, limit=10, token="invalid-token")

    assert mock_paginated.call_args.kwargs["exclude_group_ids"] is None


def test_list_public_groups_does_not_filter_by_language_and_falls_back_metadata():
    group = _make_group(group_type=AuthorGroupType.COMMUNITY)
    meta_en = MagicMock()
    meta_en.id = uuid4()
    meta_en.title = "English Community"
    meta_en.description = "EN desc"
    meta_en.sub_title = None
    meta_en.description_long = None
    meta_en.language = "EN"
    group.metadata_entries = [meta_en]

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.get_groups_paginated",
        return_value=([group], 1),
    ) as mock_paginated, patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={group.id: 0},
    ), patch(
        "pecha_api.plans.groups.groups_service.get_joiners_count_map",
        return_value={group.id: 0},
    ):
        _session_local_context(mock_session)
        result = list_public_groups(
            skip=0,
            limit=10,
            language="bo",
            group_type=AuthorGroupType.COMMUNITY,
        )

    assert "language" not in mock_paginated.call_args.kwargs
    assert result.total == 1
    assert result.groups[0].metadata.title == "English Community"
    assert result.groups[0].metadata.language == "EN"


def test_list_public_groups_returns_page_type_with_language_fallback():
    group = _make_group(group_type=AuthorGroupType.PAGE)
    meta_en = MagicMock()
    meta_en.id = uuid4()
    meta_en.title = "English Author Group"
    meta_en.description = "EN desc"
    meta_en.sub_title = None
    meta_en.description_long = None
    meta_en.language = "EN"
    group.metadata_entries = [meta_en]

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.get_groups_paginated",
        return_value=([group], 1),
    ) as mock_paginated, patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={group.id: 2},
    ), patch(
        "pecha_api.plans.groups.groups_service.get_joiners_count_map",
        return_value={group.id: 0},
    ):
        _session_local_context(mock_session)
        result = list_public_groups(
            skip=0,
            limit=10,
            language="bo",
            group_type=AuthorGroupType.PAGE,
        )

    assert "language" not in mock_paginated.call_args.kwargs
    assert mock_paginated.call_args.kwargs["group_type"] == AuthorGroupType.PAGE
    assert result.groups[0].metadata.title == "English Author Group"
    assert result.groups[0].metadata.language == "EN"


def test_list_public_groups_mixed_metadata_uses_selected_language_then_en_fallback():
    group_with_bo = _make_group(group_type=AuthorGroupType.COMMUNITY)
    meta_en = MagicMock()
    meta_en.id = uuid4()
    meta_en.title = "English Community"
    meta_en.description = None
    meta_en.sub_title = None
    meta_en.description_long = None
    meta_en.language = "EN"
    meta_bo = MagicMock()
    meta_bo.id = uuid4()
    meta_bo.title = "Tibetan Community"
    meta_bo.description = None
    meta_bo.sub_title = None
    meta_bo.description_long = None
    meta_bo.language = "BO"
    group_with_bo.metadata_entries = [meta_en, meta_bo]

    group_en_only = _make_group(group_type=AuthorGroupType.COMMUNITY)
    meta_en_only = MagicMock()
    meta_en_only.id = uuid4()
    meta_en_only.title = "English Only Community"
    meta_en_only.description = None
    meta_en_only.sub_title = None
    meta_en_only.description_long = None
    meta_en_only.language = "EN"
    group_en_only.metadata_entries = [meta_en_only]

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.get_groups_paginated",
        return_value=([group_with_bo, group_en_only], 2),
    ), patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={group_with_bo.id: 0, group_en_only.id: 0},
    ), patch(
        "pecha_api.plans.groups.groups_service.get_joiners_count_map",
        return_value={group_with_bo.id: 0, group_en_only.id: 0},
    ):
        _session_local_context(mock_session)
        result = list_public_groups(
            skip=0,
            limit=10,
            language="bo",
            group_type=AuthorGroupType.COMMUNITY,
        )

    assert result.total == 2
    assert result.groups[0].metadata.title == "Tibetan Community"
    assert result.groups[0].metadata.language == "BO"
    assert result.groups[1].metadata.title == "English Only Community"
    assert result.groups[1].metadata.language == "EN"


def _make_series_with_metadata():
    meta_en = MagicMock()
    meta_en.id = uuid4()
    meta_en.title = "English Series"
    meta_en.description = None
    meta_en.language = LanguageCode.EN
    meta_bo = MagicMock()
    meta_bo.id = uuid4()
    meta_bo.title = "Tibetan Series"
    meta_bo.description = None
    meta_bo.language = LanguageCode.BO

    series = MagicMock()
    series.id = uuid4()
    series.metadata_entries = [meta_en, meta_bo]
    series.image = None
    series.author_id = uuid4()
    series.featured = False
    series.status = MagicMock(value="PUBLISHED")
    return series


def test_series_to_dtos_returns_empty_for_empty_series_list():
    mock_db = MagicMock()
    assert _series_to_dtos(db=mock_db, series_list=[], group_id=uuid4()) == []
    mock_db.assert_not_called()


def test_group_series_list_item_dto_excludes_series_partner_id():
    assert "series_partner_id" not in GroupSeriesListItemDTO.model_fields
    assert "is_group_enrolled" in GroupSeriesListItemDTO.model_fields


def test_is_series_enrolled_for_group_context():
    partner_id = uuid4()
    assert _is_series_enrolled_for_group_context(
        partner_id, partner_id, is_enrolled_in_series=True
    )
    assert not _is_series_enrolled_for_group_context(
        partner_id, uuid4(), is_enrolled_in_series=True
    )
    assert _is_series_enrolled_for_group_context(
        None, None, is_enrolled_in_series=True
    ) is None
    assert not _is_series_enrolled_for_group_context(
        partner_id, None, is_enrolled_in_series=True
    )
    assert _is_series_enrolled_for_group_context(
        None, None, is_enrolled_in_series=False
    ) is None


def test_series_to_dtos_sets_partner_enrollment_for_authenticated_user():
    group_id = uuid4()
    series = _make_series_with_metadata()
    partner_id = uuid4()
    user_id = uuid4()
    mock_db = MagicMock()
    with patch(
        "pecha_api.plans.groups.groups_service.get_active_plan_count_map_by_series_ids",
        return_value={series.id: 2},
    ), patch(
        "pecha_api.plans.groups.groups_service.get_enrolled_count_map_by_series_ids",
        return_value={series.id: 5},
    ), patch(
        "pecha_api.plans.groups.groups_service.get_series_partner_id_map_for_group",
        return_value={series.id: partner_id},
    ), patch(
        "pecha_api.plans.groups.groups_service.get_user_series_enrollment_partner_map",
        return_value={series.id: partner_id},
    ):
        dtos = _series_to_dtos(
            db=mock_db,
            series_list=[series],
            group_id=group_id,
            user_id=user_id,
        )

    assert dtos[0].is_group_enrolled is True


def test_series_to_dtos_is_not_enrolled_without_user():
    group_id = uuid4()
    series = _make_series_with_metadata()
    partner_id = uuid4()
    mock_db = MagicMock()
    with patch(
        "pecha_api.plans.groups.groups_service.get_active_plan_count_map_by_series_ids",
        return_value={series.id: 2},
    ), patch(
        "pecha_api.plans.groups.groups_service.get_enrolled_count_map_by_series_ids",
        return_value={series.id: 5},
    ), patch(
        "pecha_api.plans.groups.groups_service.get_series_partner_id_map_for_group",
        return_value={series.id: partner_id},
    ), patch(
        "pecha_api.plans.groups.groups_service.get_user_series_enrollment_partner_map",
    ) as mock_enrollment_map:
        dtos = _series_to_dtos(
            db=mock_db,
            series_list=[series],
            group_id=group_id,
        )

    mock_enrollment_map.assert_not_called()
    assert dtos[0].is_group_enrolled is None


def test_series_to_dtos_filters_metadata_by_language():
    group_id = uuid4()
    series = _make_series_with_metadata()
    mock_db = MagicMock()
    with patch(
        "pecha_api.plans.groups.groups_service.get_active_plan_count_map_by_series_ids",
        return_value={series.id: 2},
    ), patch(
        "pecha_api.plans.groups.groups_service.get_series_partner_id_map_for_group",
        return_value={},
    ):
        all_metadata = _series_to_dtos(db=mock_db, series_list=[series], group_id=group_id)
        bo_metadata = _series_to_dtos(db=mock_db, series_list=[series], group_id=group_id, language="bo")
        missing_metadata = _series_to_dtos(db=mock_db, series_list=[series], group_id=group_id, language="zh")

    assert len(all_metadata[0].metadata) == 2
    assert bo_metadata[0].metadata.title == "Tibetan Series"
    assert bo_metadata[0].metadata.language == "BO"
    assert bo_metadata[0].plan_count == 2
    # No metadata for the requested language falls back to English.
    assert missing_metadata[0].metadata.title == "English Series"
    assert missing_metadata[0].metadata.language == "EN"


def test_group_detail_series_metadata_filtered_by_language():
    group = _make_group()
    series = _make_series_with_metadata()

    mock_db = MagicMock()
    with patch(
        "pecha_api.plans.groups.groups_service.get_series_by_group_id",
        return_value=[series],
    ), patch(
        "pecha_api.plans.groups.groups_service.get_plans_by_group_id",
        return_value=[],
    ), patch(
        "pecha_api.plans.groups.groups_service.get_active_plan_count_map_by_series_ids",
        return_value={series.id: 0},
    ), patch(
        "pecha_api.plans.groups.groups_service.get_series_partner_id_map_for_group",
        return_value={},
    ):
        detail_all = _group_to_detail(group, db=mock_db)
        detail_bo = _group_to_detail(group, db=mock_db, language="bo")

    assert len(detail_all.series[0].metadata) == 2
    assert detail_bo.series[0].metadata.title == "Tibetan Series"
    assert detail_bo.series[0].metadata.language == "BO"


def test_get_author_group_detail_series_metadata_filtered_by_language():
    group = _make_group()
    series = _make_series_with_metadata()

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={group.id: 1},
    ), patch(
        "pecha_api.plans.groups.groups_service.get_series_by_group_id",
        return_value=[series],
    ), patch(
        "pecha_api.plans.groups.groups_service.get_plans_by_group_id",
        return_value=[],
    ), patch(
        "pecha_api.plans.groups.groups_service.get_active_plan_count_map_by_series_ids",
        return_value={series.id: 0},
    ):
        _session_local_context(mock_session)
        result = get_author_group_detail(group_id=group.id, language="bo")

    assert result.series[0].metadata.title == "Tibetan Series"
    assert result.series[0].metadata.language == "BO"


def test_get_cms_group_detail_series_metadata_filtered_by_language():
    author = _make_author(is_admin=True)
    group = _make_group()
    series = _make_series_with_metadata()

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={group.id: 2},
    ), patch(
        "pecha_api.plans.groups.groups_service.get_series_by_group_id",
        return_value=[series],
    ), patch(
        "pecha_api.plans.groups.groups_service.get_plans_by_group_id",
        return_value=[],
    ), patch(
        "pecha_api.plans.groups.groups_service.get_active_plan_count_map_by_series_ids",
        return_value={series.id: 0},
    ):
        _session_local_context(mock_session)
        result = get_cms_group_detail(token="t", group_id=group.id, language="bo")

    assert result.series[0].metadata.title == "Tibetan Series"
    assert result.series[0].metadata.language == "BO"


def test_group_summary_metadata_filtered_by_language():
    from pecha_api.plans.groups.groups_service import _group_to_summary

    group = _make_group()
    meta_en = MagicMock()
    meta_en.id = uuid4()
    meta_en.title = "English Group"
    meta_en.description = "EN desc"
    meta_en.language = "EN"
    meta_bo = MagicMock()
    meta_bo.id = uuid4()
    meta_bo.title = "Tibetan Group"
    meta_bo.description = "BO desc"
    meta_bo.language = "BO"
    group.metadata_entries = [meta_en, meta_bo]
    group.tags = []
    group.members = []

    summary_all = _group_to_summary(group)
    summary_bo = _group_to_summary(group, language="bo")

    assert len(summary_all.metadata) == 2
    assert summary_bo.metadata.title == "Tibetan Group"
    assert summary_bo.metadata.language == "BO"


def test_group_summary_metadata_falls_back_to_en_when_language_missing():
    from pecha_api.plans.groups.groups_service import _group_to_summary

    group = _make_group()
    meta_en = MagicMock()
    meta_en.id = uuid4()
    meta_en.title = "English Group"
    meta_en.description = "EN desc"
    meta_en.language = "EN"
    group.metadata_entries = [meta_en]
    group.tags = []
    group.members = []

    # Requesting 'bo' which is absent -> falls back to EN, never blank.
    summary_bo = _group_to_summary(group, language="bo")

    assert summary_bo.metadata is not None
    assert summary_bo.metadata.title == "English Group"
    assert summary_bo.metadata.language == "EN"


def test_group_detail_metadata_falls_back_to_en_when_language_missing():
    from pecha_api.plans.groups.groups_service import _group_to_detail

    group = _make_group()
    meta_en = MagicMock()
    meta_en.id = uuid4()
    meta_en.title = "English Group"
    meta_en.description = "EN desc"
    meta_en.language = "EN"
    group.metadata_entries = [meta_en]
    group.tags = []
    group.members = []
    group.social_links = []

    # db=None skips series/plans loading; we only assert metadata fallback here.
    detail_bo = _group_to_detail(group, language="bo")

    assert detail_bo.metadata is not None
    assert detail_bo.metadata.title == "English Group"
    assert detail_bo.metadata.language == "EN"


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


def test_get_followed_group_returns_group_when_following():
    user = MagicMock()
    user.id = uuid4()
    group = _make_group()
    meta = MagicMock()
    meta.id = uuid4()
    meta.title = "Followed Group"
    meta.description = None
    meta.language = "EN"
    group.metadata_entries = [meta]

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_user_details",
        return_value=user,
    ), patch(
        "pecha_api.plans.groups.groups_service.is_user_following_group",
        return_value=True,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={group.id: 5},
    ):
        _session_local_context(mock_session)
        result = get_followed_group(token="t", group_id=group.id)

    assert result.id == group.id
    assert result.follower_count == 5


def test_get_followed_group_returns_404_when_not_following():
    user = MagicMock()
    user.id = uuid4()
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_user_details",
        return_value=user,
    ), patch(
        "pecha_api.plans.groups.groups_service.is_user_following_group",
        return_value=False,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            get_followed_group(token="t", group_id=uuid4())
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.detail == GROUP_NOT_FOUND


def test_get_followed_group_returns_404_when_group_missing():
    user = MagicMock()
    user.id = uuid4()
    group_id = uuid4()
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_user_details",
        return_value=user,
    ), patch(
        "pecha_api.plans.groups.groups_service.is_user_following_group",
        return_value=True,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=None,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            get_followed_group(token="t", group_id=group_id)
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.detail == GROUP_NOT_FOUND


def test_join_group_requires_public_group():
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
            join_group(token="t", group_id=uuid4())
    assert exc.value.detail == GROUP_NOT_FOUND


def test_follow_group_rejects_community_type():
    user = MagicMock()
    user.id = uuid4()
    group = _make_group(is_public=True, group_type=AuthorGroupType.COMMUNITY)

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_user_details",
        return_value=user,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            follow_group(token="t", group_id=group.id)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_join_group_rejects_page_type():
    user = MagicMock()
    user.id = uuid4()
    group = _make_group(is_public=True, group_type=AuthorGroupType.PAGE)

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_user_details",
        return_value=user,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            join_group(token="t", group_id=group.id)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_join_group_success():
    user = MagicMock()
    user.id = uuid4()
    group = _make_group(is_public=True, group_type=AuthorGroupType.COMMUNITY)

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_user_details",
        return_value=user,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.upsert_group_join",
    ) as mock_join:
        _session_local_context(mock_session)
        join_group(token="t", group_id=group.id)
    mock_join.assert_called_once()


def test_leave_group_calls_repository():
    user = MagicMock()
    user.id = uuid4()
    group_id = uuid4()
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_user_details",
        return_value=user,
    ), patch(
        "pecha_api.plans.groups.groups_service.leave_group_membership",
    ) as mock_leave_membership:
        mock_db = _session_local_context(mock_session)
        leave_group(token="t", group_id=group_id)
    mock_leave_membership.assert_called_once_with(
        db=mock_db,
        user_id=user.id,
        group_id=group_id,
    )


def test_list_joined_groups():
    user = MagicMock()
    user.id = uuid4()
    group = _make_group()
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_user_details",
        return_value=user,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_joined_group_ids_by_user",
        return_value=[group.id],
    ), patch(
        "pecha_api.plans.groups.groups_service.get_groups_paginated",
        return_value=([group], 1),
    ), patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={},
    ):
        _session_local_context(mock_session)
        result = list_joined_groups(token="t", skip=0, limit=20)
    assert result.total == 1


def test_get_joined_group_returns_group_when_joined():
    user = MagicMock()
    user.id = uuid4()
    group = _make_group()
    meta = MagicMock()
    meta.id = uuid4()
    meta.title = "Joined Group"
    meta.sub_title = None
    meta.description = None
    meta.language = "en"
    group.metadata_entries = [meta]

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_user_details",
        return_value=user,
    ), patch(
        "pecha_api.plans.groups.groups_service.is_user_joined_group",
        return_value=True,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_joiners_count_map",
        return_value={group.id: 3},
    ):
        _session_local_context(mock_session)
        result = get_joined_group(token="t", group_id=group.id)

    assert result.id == group.id
    assert result.joiner_count == 3


def test_get_joined_group_returns_404_when_not_joined():
    user = MagicMock()
    user.id = uuid4()
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_user_details",
        return_value=user,
    ), patch(
        "pecha_api.plans.groups.groups_service.is_user_joined_group",
        return_value=False,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            get_joined_group(token="t", group_id=uuid4())
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.detail == GROUP_NOT_FOUND


def test_create_group_member_invite_creates_notification():
    author = _make_author()
    group = _make_group()
    target_author = MagicMock()
    target_author.id = uuid4()
    invite = MagicMock()
    invite.id = uuid4()
    invite.group_id = group.id
    invite.target_email = "invitee@example.org"
    invite.role = AuthorGroupMemberRole.AUTHOR
    invite.status = AuthorGroupInviteStatus.PENDING.value
    invite.expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    invite.created_at = datetime.now(timezone.utc)
    invite.created_by = author.email
    invite.accepted_at = None
    invite.rejected_at = None
    invite.revoked_at = None

    notification = MagicMock()
    notification.id = uuid4()

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        side_effect=lambda db, group_id, author_id: (
            MagicMock(role=AuthorGroupMemberRole.OWNER) if author_id == author.id else None
        ),
    ), patch(
        "pecha_api.plans.groups.groups_service.get_author_by_email",
        return_value=target_author,
    ), patch(
        "pecha_api.plans.groups.groups_service.has_pending_invite",
        return_value=False,
    ), patch(
        "pecha_api.plans.groups.groups_service.create_group_invite",
        return_value=invite,
    ), patch(
        "pecha_api.plans.groups.groups_service.create_notification_record",
        return_value=notification,
    ), patch(
        "pecha_api.plans.groups.groups_service.send_group_invitation_email",
    ):
        _session_local_context(mock_session)
        result = create_group_member_invite(
            token="t",
            group_id=group.id,
            request=CreateGroupInviteRequest(
                target_email="invitee@example.org",
                role=AuthorGroupMemberRole.AUTHOR,
            ),
        )
    assert result.invite.target_email == "invitee@example.org"
    assert result.notification_id == notification.id


def test_create_group_member_invite_blocks_existing_member():
    author = _make_author()
    group = _make_group()
    target_author = MagicMock()
    target_author.id = uuid4()

    def _get_member(db, group_id, author_id):
        if author_id == author.id:
            return MagicMock(role=AuthorGroupMemberRole.OWNER)
        if author_id == target_author.id:
            return MagicMock(role=AuthorGroupMemberRole.AUTHOR)
        return None

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        side_effect=_get_member,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_author_by_email",
        return_value=target_author,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            create_group_member_invite(
                token="t",
                group_id=group.id,
                request=CreateGroupInviteRequest(
                    target_email="invitee@example.org",
                    role=AuthorGroupMemberRole.AUTHOR,
                ),
            )
    assert "already a member" in exc.value.detail.lower()


def test_create_group_member_invite_cannot_invite_as_owner():
    author = _make_author()
    group = _make_group()

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        return_value=MagicMock(role=AuthorGroupMemberRole.OWNER),
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            create_group_member_invite(
                token="t",
                group_id=group.id,
                request=CreateGroupInviteRequest(
                    target_email="invitee@example.org",
                    role=AuthorGroupMemberRole.OWNER,
                ),
            )
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.value.detail == OWNER_ROLE_NOT_ASSIGNABLE


def test_create_group_member_invite_admin_cannot_invite_as_admin():
    author = _make_author()
    group = _make_group()

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        return_value=MagicMock(role=AuthorGroupMemberRole.ADMIN),
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            create_group_member_invite(
                token="t",
                group_id=group.id,
                request=CreateGroupInviteRequest(
                    target_email="invitee@example.org",
                    role=AuthorGroupMemberRole.ADMIN,
                ),
            )
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_update_group_member_role_admin_cannot_assign_admin_to_other():
    author = _make_author()
    group = _make_group()
    target_id = uuid4()
    current = MagicMock()
    current.role = AuthorGroupMemberRole.ADMIN
    target = MagicMock()
    target.role = AuthorGroupMemberRole.AUTHOR

    def _get_member(db, group_id, author_id):
        if author_id == author.id:
            return current
        if author_id == target_id:
            return target
        return None

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        side_effect=_get_member,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            update_group_member_role(
                token="t",
                group_id=group.id,
                author_id=target_id,
                request=UpdateGroupMemberRoleRequest(role=AuthorGroupMemberRole.ADMIN),
            )
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_create_group_member_invite_blocks_pending_invite():
    author = _make_author()
    group = _make_group()
    target_author = MagicMock()
    target_author.id = uuid4()

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        side_effect=lambda db, group_id, author_id: (
            MagicMock(role=AuthorGroupMemberRole.OWNER) if author_id == author.id else None
        ),
    ), patch(
        "pecha_api.plans.groups.groups_service.get_author_by_email",
        return_value=target_author,
    ), patch(
        "pecha_api.plans.groups.groups_service.has_pending_invite",
        return_value=True,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            create_group_member_invite(
                token="t",
                group_id=group.id,
                request=CreateGroupInviteRequest(
                    target_email="invitee@example.org",
                    role=AuthorGroupMemberRole.AUTHOR,
                ),
            )
    assert "pending invitation" in exc.value.detail.lower()


def test_accept_group_invite_email_mismatch():
    author = _make_author(email="other@example.org")
    invite = MagicMock()
    invite.target_email = "invitee@example.org"
    invite.status = AuthorGroupInviteStatus.PENDING.value
    invite.expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_invite_by_id",
        return_value=invite,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            accept_group_invite_by_id(token="t", invite_id=uuid4())
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_accept_group_invite_expired():
    author = _make_author(email="invitee@example.org")
    invite = MagicMock()
    invite.target_email = "invitee@example.org"
    invite.status = AuthorGroupInviteStatus.PENDING.value
    invite.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_invite_by_id",
        return_value=invite,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            accept_group_invite_by_id(token="t", invite_id=uuid4())
    assert "expired" in exc.value.detail.lower()


def test_accept_group_invite_success_adds_member():
    author = _make_author(email="invitee@example.org")
    group = _make_group()
    invite = MagicMock()
    invite.target_email = "invitee@example.org"
    invite.status = AuthorGroupInviteStatus.PENDING.value
    invite.expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    invite.role = AuthorGroupMemberRole.AUTHOR
    invite.group_id = group.id
    invite.id = uuid4()

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_invite_by_id",
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
        "pecha_api.plans.groups.groups_service.save_invite",
    ), patch(
        "pecha_api.plans.groups.groups_service._mark_invite_notification_read",
    ), patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={},
    ):
        _session_local_context(mock_session)
        accept_group_invite_by_id(token="t", invite_id=invite.id)
    mock_add.assert_called_once()


def test_update_group_member_role_cannot_promote_to_owner():
    author = _make_author()
    group = _make_group()
    current = MagicMock()
    current.role = AuthorGroupMemberRole.ADMIN
    target = MagicMock()
    target.role = AuthorGroupMemberRole.ADMIN

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        side_effect=lambda db, group_id, author_id: target if author_id == author.id else current,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            update_group_member_role(
                token="t",
                group_id=group.id,
                author_id=author.id,
                request=UpdateGroupMemberRoleRequest(role=AuthorGroupMemberRole.OWNER),
            )
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.value.detail == OWNER_ROLE_NOT_ASSIGNABLE


def test_update_group_member_role_blocks_last_owner_demotion():
    author = _make_author()
    group = _make_group()
    target_id = uuid4()
    target = MagicMock()
    target.role = AuthorGroupMemberRole.OWNER
    current = MagicMock()
    current.role = AuthorGroupMemberRole.OWNER

    def _get_member(db, group_id, author_id):
        if author_id == author.id:
            return current
        if author_id == target_id:
            return target
        return None

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        side_effect=_get_member,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_owner_count",
        return_value=1,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            update_group_member_role(
                token="t",
                group_id=group.id,
                author_id=target_id,
                request=UpdateGroupMemberRoleRequest(role=AuthorGroupMemberRole.ADMIN),
            )
    assert "OWNER" in exc.value.detail


def test_delete_group_member_blocks_last_owner_removal():
    author = _make_author(is_admin=True)
    group = _make_group()
    target = MagicMock()
    target.role = AuthorGroupMemberRole.OWNER

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        return_value=target,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_owner_count",
        return_value=1,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            delete_group_member(token="t", group_id=group.id, author_id=uuid4())
    assert "owner" in exc.value.detail.lower()


def test_delete_group_member_self_remove_as_author():
    author = _make_author()
    group = _make_group()
    member = MagicMock()
    member.role = AuthorGroupMemberRole.AUTHOR

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        return_value=member,
    ), patch(
        "pecha_api.plans.groups.groups_service.remove_group_member",
    ) as mock_remove:
        _session_local_context(mock_session)
        delete_group_member(token="t", group_id=group.id, author_id=author.id)
    mock_remove.assert_called_once()


def test_delete_group_member_self_remove_last_owner_blocked():
    author = _make_author()
    group = _make_group()
    member = MagicMock()
    member.role = AuthorGroupMemberRole.OWNER

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        return_value=member,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_owner_count",
        return_value=1,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            delete_group_member(token="t", group_id=group.id, author_id=author.id)
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST


def test_delete_group_member_admin_cannot_remove_owner():
    author = _make_author()
    group = _make_group()
    target_id = uuid4()
    target = MagicMock()
    target.role = AuthorGroupMemberRole.OWNER
    current = MagicMock()
    current.role = AuthorGroupMemberRole.ADMIN

    def _get_member(db, group_id, author_id):
        if author_id == target_id:
            return target
        if author_id == author.id:
            return current
        return None

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        side_effect=_get_member,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            delete_group_member(token="t", group_id=group.id, author_id=target_id)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


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


def test_replace_group_social_links_by_id_delegates_to_repository():
    author = _make_author()
    group = _make_group()
    current = MagicMock()
    current.role = AuthorGroupMemberRole.ADMIN
    loaded = _make_group()

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


def test_reject_group_invite_by_id_success():
    author = _make_author(email="invitee@example.org")
    invite = MagicMock()
    invite.target_email = "invitee@example.org"
    invite.status = AuthorGroupInviteStatus.PENDING.value
    invite.expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    invite.id = uuid4()
    invite.group_id = uuid4()
    invite.role = AuthorGroupMemberRole.AUTHOR
    invite.group = None
    invite.created_at = datetime.now(timezone.utc)
    invite.created_by = "owner@example.org"
    invite.accepted_at = None
    invite.rejected_at = None
    invite.revoked_at = None

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_invite_by_id",
        return_value=invite,
    ), patch(
        "pecha_api.plans.groups.groups_service.save_invite",
    ), patch(
        "pecha_api.plans.groups.groups_service._mark_invite_notification_read",
    ):
        _session_local_context(mock_session)
        result = reject_group_invite_by_id(token="t", invite_id=invite.id)
    assert result.status == AuthorGroupInviteStatus.REJECTED


def test_list_my_pending_group_invites():
    author = _make_author(email="invitee@example.org")
    invite = MagicMock()
    invite.target_email = "invitee@example.org"
    invite.status = AuthorGroupInviteStatus.PENDING.value
    invite.expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    invite.id = uuid4()
    invite.group_id = uuid4()
    invite.role = AuthorGroupMemberRole.AUTHOR.value
    invite.group = MagicMock()
    invite.group.metadata_entries = []
    invite.accepted_at = None
    invite.rejected_at = None
    invite.revoked_at = None
    invite.created_at = datetime.now(timezone.utc)
    invite.created_by = "owner@example.org"

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.list_pending_invites_by_email",
        return_value=[invite],
    ):
        _session_local_context(mock_session)
        result = list_my_pending_group_invites(token="t")
    assert result.total == 1


def test_list_group_invites_as_admin_member():
    author = _make_author()
    group = _make_group()
    current = MagicMock()
    current.role = AuthorGroupMemberRole.ADMIN
    invite = MagicMock()
    invite.id = uuid4()
    invite.group_id = group.id
    invite.target_email = "invitee@example.org"
    invite.role = AuthorGroupMemberRole.AUTHOR.value
    invite.status = AuthorGroupInviteStatus.PENDING.value
    invite.expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    invite.accepted_at = None
    invite.rejected_at = None
    invite.revoked_at = None
    invite.created_at = datetime.now(timezone.utc)
    invite.created_by = author.email
    invite.group = group
    group.metadata_entries = []

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
        "pecha_api.plans.groups.groups_service.list_invites_by_group",
        return_value=[invite],
    ):
        _session_local_context(mock_session)
        result = list_group_invites(token="t", group_id=group.id, status_filter=None)
    assert result.total == 1


def test_revoke_group_invite_success():
    author = _make_author()
    group = _make_group()
    current = MagicMock()
    current.role = AuthorGroupMemberRole.OWNER
    invite = MagicMock()
    invite.id = uuid4()
    invite.group_id = group.id
    invite.role = AuthorGroupMemberRole.AUTHOR.value
    invite.status = AuthorGroupInviteStatus.PENDING.value
    invite.target_email = "invitee@example.org"
    target_author = MagicMock()
    target_author.id = uuid4()

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
        return_value=invite,
    ), patch(
        "pecha_api.plans.groups.groups_service.revoke_invite",
    ) as mock_revoke, patch(
        "pecha_api.plans.groups.groups_service.get_author_by_email",
        return_value=target_author,
    ), patch(
        "pecha_api.plans.groups.groups_service._mark_invite_notification_read",
    ):
        _session_local_context(mock_session)
        revoke_group_invite(token="t", group_id=group.id, invite_id=invite.id)
    mock_revoke.assert_called_once()


def test_create_group_member_invite_builds_notification_with_group_title():
    author = _make_author()
    author.first_name = "Jane"
    author.last_name = "Doe"
    group = _make_group()
    metadata = MagicMock()
    metadata.language = LanguageCode.EN
    metadata.title = "English Group"
    loaded_group = _make_group()
    loaded_group.metadata_entries = [metadata]
    target_author = MagicMock()
    target_author.id = uuid4()
    invite = MagicMock()
    invite.id = uuid4()
    invite.group_id = group.id
    invite.target_email = "invitee@example.org"
    invite.role = AuthorGroupMemberRole.AUTHOR
    invite.status = AuthorGroupInviteStatus.PENDING.value
    invite.expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    invite.created_at = datetime.now(timezone.utc)
    invite.created_by = author.email
    invite.accepted_at = None
    invite.rejected_at = None
    invite.revoked_at = None
    notification = MagicMock()
    notification.id = uuid4()

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        side_effect=[group, loaded_group],
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        side_effect=lambda db, group_id, author_id: (
            MagicMock(role=AuthorGroupMemberRole.OWNER)
            if author_id == author.id
            else None
        ),
    ), patch(
        "pecha_api.plans.groups.groups_service.get_author_by_email",
        return_value=target_author,
    ), patch(
        "pecha_api.plans.groups.groups_service.has_pending_invite",
        return_value=False,
    ), patch(
        "pecha_api.plans.groups.groups_service.create_group_invite",
        return_value=invite,
    ), patch(
        "pecha_api.plans.groups.groups_service.create_notification_record",
        return_value=notification,
    ) as mock_notify, patch(
        "pecha_api.plans.groups.groups_service.send_group_invitation_email",
    ):
        _session_local_context(mock_session)
        create_group_member_invite(
            token="t",
            group_id=group.id,
            request=CreateGroupInviteRequest(
                target_email="invitee@example.org",
                role=AuthorGroupMemberRole.AUTHOR,
            ),
        )
    assert mock_notify.call_args.kwargs["title"] == "Invitation to join English Group"
    assert "Jane Doe" in mock_notify.call_args.kwargs["description"]


def test_create_group_member_invite_requires_target_email():
    author = _make_author()
    group = _make_group()
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        return_value=MagicMock(role=AuthorGroupMemberRole.OWNER),
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            create_group_member_invite(
                token="t",
                group_id=group.id,
                request=CreateGroupInviteRequest(target_email="   ", role=AuthorGroupMemberRole.AUTHOR),
            )
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST


def test_create_group_member_invite_unknown_target_email():
    author = _make_author()
    group = _make_group()
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
        "pecha_api.plans.groups.groups_service.get_author_by_email",
        return_value=None,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            create_group_member_invite(
                token="t",
                group_id=group.id,
                request=CreateGroupInviteRequest(
                    target_email="missing@example.org",
                    role=AuthorGroupMemberRole.AUTHOR,
                ),
            )
    assert "No registered author" in exc.value.detail


def test_accept_group_invite_group_missing_after_invite_found():
    author = _make_author(email="invitee@example.org")
    invite = MagicMock()
    invite.target_email = "invitee@example.org"
    invite.status = AuthorGroupInviteStatus.PENDING.value
    invite.expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    invite.group_id = uuid4()

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_invite_by_id",
        return_value=invite,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=None,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            accept_group_invite_by_id(token="t", invite_id=uuid4())
    assert exc.value.detail == GROUP_NOT_FOUND


def test_accept_group_invite_skips_add_when_already_member():
    author = _make_author(email="invitee@example.org")
    group = _make_group()
    invite = MagicMock()
    invite.target_email = "invitee@example.org"
    invite.status = AuthorGroupInviteStatus.PENDING.value
    invite.expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    invite.role = AuthorGroupMemberRole.AUTHOR
    invite.group_id = group.id
    invite.id = uuid4()
    existing = MagicMock()

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_invite_by_id",
        return_value=invite,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        return_value=existing,
    ), patch(
        "pecha_api.plans.groups.groups_service.add_group_member",
    ) as mock_add, patch(
        "pecha_api.plans.groups.groups_service.save_invite",
    ), patch(
        "pecha_api.plans.groups.groups_service._mark_invite_notification_read",
    ), patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={},
    ):
        _session_local_context(mock_session)
        accept_group_invite_by_id(token="t", invite_id=invite.id)
    mock_add.assert_not_called()


def test_list_group_invites_group_not_found():
    author = _make_author()
    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=None,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            list_group_invites(token="t", group_id=uuid4(), status_filter=None)
    assert exc.value.detail == GROUP_NOT_FOUND


def test_revoke_group_invite_not_pending():
    author = _make_author()
    group = _make_group()
    current = MagicMock()
    current.role = AuthorGroupMemberRole.OWNER
    invite = MagicMock()
    invite.id = uuid4()
    invite.group_id = group.id
    invite.role = AuthorGroupMemberRole.AUTHOR.value
    invite.status = AuthorGroupInviteStatus.ACCEPTED.value

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
        return_value=invite,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            revoke_group_invite(token="t", group_id=group.id, invite_id=invite.id)
    assert "pending" in exc.value.detail.lower()


def test_revoke_group_invite_wrong_group():
    author = _make_author()
    group = _make_group()
    current = MagicMock()
    current.role = AuthorGroupMemberRole.OWNER
    invite = MagicMock()
    invite.id = uuid4()
    invite.group_id = uuid4()
    invite.role = AuthorGroupMemberRole.AUTHOR.value
    invite.status = AuthorGroupInviteStatus.PENDING.value

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
        return_value=invite,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            revoke_group_invite(token="t", group_id=group.id, invite_id=invite.id)
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_revoke_group_invite_admin_cannot_revoke_admin_invite():
    author = _make_author()
    group = _make_group()
    current = MagicMock()
    current.role = AuthorGroupMemberRole.ADMIN
    invite = MagicMock()
    invite.id = uuid4()
    invite.group_id = group.id
    invite.role = AuthorGroupMemberRole.ADMIN.value
    invite.status = AuthorGroupInviteStatus.PENDING.value

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
        return_value=invite,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            revoke_group_invite(token="t", group_id=group.id, invite_id=invite.id)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_update_group_member_role_cannot_assign_owner():
    author = _make_author()
    group = _make_group()
    target_id = uuid4()
    current = MagicMock()
    current.role = AuthorGroupMemberRole.OWNER
    target = MagicMock()
    target.role = AuthorGroupMemberRole.ADMIN

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        side_effect=lambda db, group_id, author_id: current if author_id == author.id else target,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            update_group_member_role(
                token="t",
                group_id=group.id,
                author_id=target_id,
                request=UpdateGroupMemberRoleRequest(role=AuthorGroupMemberRole.OWNER),
            )
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.value.detail == OWNER_ROLE_NOT_ASSIGNABLE


def test_transfer_group_ownership_success():
    owner = _make_author()
    group = _make_group()
    new_owner_id = uuid4()
    owner_member = MagicMock()
    owner_member.role = AuthorGroupMemberRole.OWNER
    new_member = MagicMock()
    new_member.role = AuthorGroupMemberRole.ADMIN
    loaded = _make_group()

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=owner,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        side_effect=[group, loaded],
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        side_effect=lambda db, group_id, author_id: (
            owner_member if author_id == owner.id else new_member
        ),
    ), patch(
        "pecha_api.plans.groups.groups_service.set_group_member_role",
    ) as mock_set_role, patch(
        "pecha_api.plans.groups.groups_service.get_followers_count_map",
        return_value={},
    ):
        _session_local_context(mock_session)
        transfer_group_ownership(
            token="t",
            group_id=group.id,
            new_owner_author_id=new_owner_id,
        )
    assert mock_set_role.call_count == 2


def test_transfer_group_ownership_requires_current_owner():
    author = _make_author()
    group = _make_group()
    admin_member = MagicMock()
    admin_member.role = AuthorGroupMemberRole.ADMIN

    with patch("pecha_api.plans.groups.groups_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.groups_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_by_id",
        return_value=group,
    ), patch(
        "pecha_api.plans.groups.groups_service.get_group_member",
        return_value=admin_member,
    ):
        _session_local_context(mock_session)
        with pytest.raises(HTTPException) as exc:
            transfer_group_ownership(
                token="t",
                group_id=group.id,
                new_owner_author_id=uuid4(),
            )
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
