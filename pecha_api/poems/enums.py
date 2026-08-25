import enum

from sqlalchemy import Enum


class PoemStatus(enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


PoemStatusEnum = Enum(
    PoemStatus,
    name="poem_status",
)
