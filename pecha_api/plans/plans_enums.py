import enum
from sqlalchemy import Enum

class DifficultyLevel(enum.Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"

class ContentType(enum.Enum):
    TEXT = "TEXT"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    IMAGE = "IMAGE"
    SOURCE_REFERENCE = "SOURCE_REFERENCE"

class UserPlanStatus(enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"

class PlanStatus(enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    UNPUBLISHED = "UNPUBLISHED"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"

class LanguageCode(enum.Enum):
    EN = "EN"
    BO = "BO"
    ZH = "ZH"

class SortOrder(enum.Enum):
    ASC = "asc"
    DESC = "desc"

class SortBy(enum.Enum):
    TOTAL_DAYS = "total_days"
    STATUS = "status"
    CREATED_AT = "created_at"

class EnrollmentSource(enum.Enum):
    DIRECT = "DIRECT"
    SERIES = "SERIES"

class SeriesStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class PlanAudioType(enum.Enum):
    RECITATION = "RECITATION"
    INSTRUCTION = "INSTRUCTION"
    TEXT_READING = "TEXT_READING"


# SQLAlchemy enum types
DifficultyLevelEnum = Enum(DifficultyLevel)
ContentTypeEnum = Enum(ContentType)
UserPlanStatusEnum = Enum(UserPlanStatus)
PlanStatusEnum = Enum(PlanStatus)
LanguageCodeEnum = Enum(LanguageCode)
EnrollmentSourceEnum = Enum(EnrollmentSource)
SeriesStatusEnum = Enum(SeriesStatus)
PlanAudioTypeEnum = Enum(PlanAudioType)


