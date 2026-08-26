import enum
from sqlalchemy import Enum


class RestrictedItemType(enum.Enum):
    MANTRA = "MANTRA"
    ACCUMULATOR = "ACCUMULATOR"
    GROUP_ACCUMULATOR = "GROUP_ACCUMULATOR"
    PLAN = "PLAN"
    SERIES = "SERIES"
    GROUP = "GROUP"
    RECITATION = "RECITATION"
    RECITATION_COLLECTION = "RECITATION_COLLECTION"
    GROUP_RECITATION_COLLECTION = "GROUP_RECITATION_COLLECTION"


RestrictedItemTypeEnum = Enum(
    RestrictedItemType,
    name="china_restricted_item_type",
)
