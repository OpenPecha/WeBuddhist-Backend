import enum
from sqlalchemy import Enum


class BookmarkType(enum.Enum):
    TEXT = "TEXT"
    PLAN = "PLAN"
    SERIES = "SERIES"
    ACCUMULATOR = "ACCUMULATOR"
    TIMER = "TIMER"
    VERSE = "VERSE"


BookmarkTypeEnum = Enum(BookmarkType, name="bookmark_type")
