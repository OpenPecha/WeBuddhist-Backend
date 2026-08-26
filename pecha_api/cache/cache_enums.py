from enum import Enum

class CacheType(Enum):
    RECITATION_DETAILS = "recitation_details"
    TEXT_DETAIL = "text_detail"
    TEXT_VERSIONS = "text_versions"
    TEXT_LANGUAGES = "text_languages"
    LANGUAGE_VERSIONS = "language_versions"
    TEXTS_BY_ID_OR_COLLECTION = "texts_by_id_or_collection"
    TEXT_TABLE_OF_CONTENTS = "text_table_of_contents"
    DETAIL_TEXT_TABLE_OF_CONTENT = "detail_text_table_of_content"

    SEGMENTS_DETAILS = "segments_details"

    GROUP_DETAIL = "group_detail"

    USER_INFO = "user_info"
    USER_DAILY_LOG = "user_daily_log"
    USER_STATS = "user_stats"

    TOPICS = "topics"
    
    # Collection-specific cache types
    COLLECTIONS = "collections"
    COLLECTION_DETAIL = "collection_detail"

    # Plan-specific cache types
    PLAN_DAY_DETAIL = "plan_day_detail"

    CALENDAR_YEAR = "calendar_year"
    