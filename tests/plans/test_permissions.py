import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from starlette import status

from pecha_api.plans.groups.groups_enums import AuthorGroupMemberRole
from pecha_api.plans.platform_enums import PlatformRole
from pecha_api.plans.plans_enums import PlanStatus
from pecha_api.plans.shared.permissions import (
    author_has_any_group,
    build_author_access_context,
    can_edit_content,
    get_platform_role,
    is_platform_read_only,
    is_reviewer,
    is_super_admin,
    require_active_author,
    require_can_change_status,
    require_can_create_content,
    require_can_edit_content,
    require_can_read_group_content,
    require_can_request_transfer,
    require_can_respond_transfer,
    require_cms_write_access,
    require_super_admin,
    require_super_admin_or_reviewer,
)


class _AuthorStub:
    def __init__(self, platform_role=PlatformRole.CREATOR, is_active=True, is_verified=True):
        self.id = uuid.uuid4()
        self.platform_role = platform_role.value if isinstance(platform_role, PlatformRole) else platform_role
        self.is_active = is_active
        self.is_verified = is_verified


def test_can_edit_content_author_draft_only():
    assert can_edit_content(AuthorGroupMemberRole.AUTHOR, PlanStatus.DRAFT) is True
    assert can_edit_content(AuthorGroupMemberRole.AUTHOR, PlanStatus.PUBLISHED) is False


def test_can_edit_content_owner_all_statuses():
    assert can_edit_content(AuthorGroupMemberRole.OWNER, PlanStatus.PUBLISHED) is True
    assert can_edit_content(AuthorGroupMemberRole.ADMIN, PlanStatus.DRAFT) is True


def test_get_platform_role_from_author():
    author = _AuthorStub(platform_role=PlatformRole.REVIEWER)
    assert get_platform_role(author) == PlatformRole.REVIEWER


def test_get_platform_role_defaults_to_creator():
    author = MagicMock()
    author.platform_role = None
    assert get_platform_role(author) == PlatformRole.CREATOR


def test_is_super_admin_and_reviewer():
    assert is_super_admin(_AuthorStub(PlatformRole.SUPER_ADMIN)) is True
    assert is_reviewer(_AuthorStub(PlatformRole.REVIEWER)) is True
    assert is_platform_read_only(_AuthorStub(PlatformRole.REVIEWER)) is True


def test_require_active_author_raises_when_inactive():
    with pytest.raises(HTTPException) as exc_info:
        require_active_author(_AuthorStub(is_active=False))
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


def test_require_super_admin_forbidden():
    with pytest.raises(HTTPException) as exc_info:
        require_super_admin(_AuthorStub(PlatformRole.CREATOR))
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


def test_require_super_admin_or_reviewer_allows_reviewer():
    require_super_admin_or_reviewer(_AuthorStub(PlatformRole.REVIEWER))


def test_require_cms_write_access_blocks_reviewer():
    with pytest.raises(HTTPException) as exc_info:
        require_cms_write_access(_AuthorStub(PlatformRole.REVIEWER))
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


def test_require_can_read_group_content_super_admin_skips_membership():
    db = MagicMock()
    require_can_read_group_content(db=db, group_id=uuid.uuid4(), author=_AuthorStub(PlatformRole.SUPER_ADMIN))


def test_require_can_read_group_content_raises_without_membership():
    db = MagicMock()
    with patch(
        "pecha_api.plans.shared.permissions.get_group_member",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            require_can_read_group_content(
                db=db,
                group_id=uuid.uuid4(),
                author=_AuthorStub(PlatformRole.CREATOR),
            )
    assert exc_info.value.detail == "NO_GROUP_MEMBERSHIP"


def test_require_can_create_content_checks_write_access():
    db = MagicMock()
    member = MagicMock(role=AuthorGroupMemberRole.AUTHOR.value)
    with patch(
        "pecha_api.plans.shared.permissions.get_group_member",
        return_value=member,
    ):
        require_can_create_content(
            db=db,
            group_id=uuid.uuid4(),
            author=_AuthorStub(PlatformRole.CREATOR),
        )


def test_require_can_edit_content_blocks_author_on_published():
    db = MagicMock()
    member = MagicMock(role=AuthorGroupMemberRole.AUTHOR.value)
    with patch(
        "pecha_api.plans.shared.permissions.get_group_member",
        return_value=member,
    ):
        with pytest.raises(HTTPException) as exc_info:
            require_can_edit_content(
                db=db,
                group_id=uuid.uuid4(),
                author=_AuthorStub(PlatformRole.CREATOR),
                content_status=PlanStatus.PUBLISHED,
            )
    assert exc_info.value.detail == "CONTENT_PUBLISHED_READ_ONLY"


def test_require_can_change_status_allows_super_admin():
    db = MagicMock()
    require_can_change_status(
        db=db,
        group_id=uuid.uuid4(),
        author=_AuthorStub(PlatformRole.SUPER_ADMIN),
    )


def test_require_can_request_and_respond_transfer_super_admin():
    db = MagicMock()
    admin = _AuthorStub(PlatformRole.SUPER_ADMIN)
    require_can_request_transfer(db=db, from_group_id=uuid.uuid4(), author=admin)
    require_can_respond_transfer(db=db, to_group_id=uuid.uuid4(), author=admin)


def test_author_has_any_group():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = MagicMock()
    assert author_has_any_group(db=db, author_id=uuid.uuid4()) is True

    db.query.return_value.filter.return_value.first.return_value = None
    assert author_has_any_group(db=db, author_id=uuid.uuid4()) is False


def test_build_author_access_context():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = MagicMock()
    author = _AuthorStub(PlatformRole.CREATOR, is_active=True, is_verified=True)
    ctx = build_author_access_context(db=db, author=author)
    assert ctx["platform_role"] == PlatformRole.CREATOR
    assert ctx["has_group"] is True
    assert ctx["can_create_content"] is True
