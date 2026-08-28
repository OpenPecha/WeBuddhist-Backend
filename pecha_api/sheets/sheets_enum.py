from enum import Enum

class SortOrder(Enum):
    ASC = "asc"
    DESC = "desc"

class SortBy(Enum):
    CREATED_DATE = "created_date"
    PUBLISHED_DATE = "published_date"
