import enum

from sqlalchemy import Enum


class AuthorGroupMemberRole(enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    AUTHOR = "AUTHOR"
    VIEWER = "VIEWER"


AuthorGroupMemberRoleEnum = Enum(
    AuthorGroupMemberRole,
    name="author_group_member_role",
)
