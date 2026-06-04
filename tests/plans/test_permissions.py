from pecha_api.plans.groups.groups_enums import AuthorGroupMemberRole
from pecha_api.plans.platform_enums import PlatformRole
from pecha_api.plans.plans_enums import PlanStatus
from pecha_api.plans.shared.permissions import can_edit_content, get_platform_role


class _AuthorStub:
    def __init__(self, platform_role=PlatformRole.CREATOR, is_active=True):
        self.platform_role = platform_role.value
        self.is_active = is_active


def test_can_edit_content_author_draft_only():
    assert can_edit_content(AuthorGroupMemberRole.AUTHOR, PlanStatus.DRAFT) is True
    assert can_edit_content(AuthorGroupMemberRole.AUTHOR, PlanStatus.PUBLISHED) is False


def test_can_edit_content_owner_all_statuses():
    assert can_edit_content(AuthorGroupMemberRole.OWNER, PlanStatus.PUBLISHED) is True
    assert can_edit_content(AuthorGroupMemberRole.ADMIN, PlanStatus.DRAFT) is True


def test_get_platform_role_from_author():
    author = _AuthorStub(platform_role=PlatformRole.REVIEWER)
    assert get_platform_role(author) == PlatformRole.REVIEWER
