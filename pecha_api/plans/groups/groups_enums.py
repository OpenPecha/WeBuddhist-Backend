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


class AuthorGroupType(enum.Enum):
    PAGE = "PAGE"
    COMMUNITY = "COMMUNITY"


AuthorGroupTypeEnum = Enum(
    AuthorGroupType,
    name="author_group_type",
)
