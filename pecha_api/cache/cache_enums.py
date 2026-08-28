from enum import Enum

class CacheType(Enum):
    RECITATION_DETAILS = "recitation_details"
    RECITATION_LIST = "recitation_list"
    TEXT_DETAIL = "text_detail"
    TEXT_VERSIONS = "text_versions"
    TEXT_LANGUAGES = "text_languages"
    LANGUAGE_VERSIONS = "language_versions"
    TEXTS_BY_ID_OR_COLLECTION = "texts_by_id_or_collection"
    TEXT_TABLE_OF_CONTENTS = "text_table_of_contents"
    DETAIL_TEXT_TABLE_OF_CONTENT = "detail_text_table_of_content"

    SEGMENTS_DETAILS = "segments_details"
    SEGMENT_INFO = "segment_info"
    SEGMENT_TRANSLATIONS = "segment_translations"
    SEGMENT_COMMENTARIES = "segment_commentaries"
    SEGMENT_ROOT_TEXT = "segment_root_text"

    GROUP_DETAIL = "group_detail"

    USER_INFO = "user_info"
    USER_DAILY_LOG = "user_daily_log"
    USER_STATS = "user_stats"

    # Collection-specific cache types
    COLLECTIONS = "collections"
    COLLECTION_DETAIL = "collection_detail"

    # Plan-specific cache types
    PLAN_DAY_DETAIL = "plan_day_detail"

    CALENDAR_YEAR = "calendar_year"
    