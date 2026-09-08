import enum

from sqlalchemy import Enum


class AuthorGroupMemberRole(enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    AUTHOR = "AUTHOR"
    VIEWER = "VIEWER"


AuthorGroupMemberRoleEnum = Enum(
    AuthorGroupMemberRole,
    name="author_group_member_role",
)


class AuthorGroupInviteStatus(enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


AuthorGroupInviteStatusEnum = Enum(
    AuthorGroupInviteStatus,
    name="author_group_invite_status",
)


class AuthorGroupJoinRequestStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


AuthorGroupJoinRequestStatusEnum = Enum(
    AuthorGroupJoinRequestStatus,
    name="author_group_join_request_status",
)


class AuthorGroupType(enum.Enum):
    PAGE = "PAGE"
    COMMUNITY = "COMMUNITY"


AuthorGroupTypeEnum = Enum(
    AuthorGroupType,
    name="author_group_type",
)


class AuthorGroupStatus(enum.Enum):
    """Whether a group reaches the app at all. Separate from is_public, which
    only decides how an already-published group is joined and read."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    UNPUBLISHED = "UNPUBLISHED"


AuthorGroupStatusEnum = Enum(
    AuthorGroupStatus,
    name="author_group_status",
)
