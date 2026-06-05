import enum

from sqlalchemy import Enum


class PlatformRole(enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    REVIEWER = "REVIEWER"
    CREATOR = "CREATOR"


PlatformRoleEnum = Enum(PlatformRole, name="platform_role")
