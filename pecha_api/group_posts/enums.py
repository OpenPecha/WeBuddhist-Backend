import enum

from sqlalchemy import Enum


class GroupPostStatus(enum.Enum):
    PUBLISHED = "PUBLISHED"
    HIDDEN = "HIDDEN"


GroupPostStatusEnum = Enum(
    GroupPostStatus,
    name="group_post_status",
)


class GroupPostMediaType(enum.Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"


GroupPostMediaTypeEnum = Enum(
    GroupPostMediaType,
    name="group_post_media_type",
)
