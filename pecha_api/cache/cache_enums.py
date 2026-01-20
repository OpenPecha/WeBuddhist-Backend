from enum import Enum

class CacheType(Enum):
    RECITATION_DETAILS = "recitation_details"
    TEXT_DETAIL = "text_detail"
    TEXT_VERSIONS = "text_versions"
    TEXTS_BY_ID_OR_COLLECTION = "texts_by_id_or_collection"
    TEXT_TABLE_OF_CONTENTS = "text_table_of_contents"
    DETAIL_TEXT_TABLE_OF_CONTENT = "detail_text_table_of_content"

    SEGMENT_DETAIL = "segment_detail"
    SEGMENTS_DETAILS = "segments_details"
    SEGMENT_INFO = "segment_info"
    SEGMENT_ROOT_TEXT = "segment_root_text"
    SEGMENT_TRANSLATIONS = "segment_translations"
    SEGMENT_COMMENTARIES = "segment_commentaries"

    GROUP_DETAIL = "group_detail"

    SHEETS = "sheets"
    SHEET_DETAIL = "sheet_detail"
    SHEET_TABLE_OF_CONTENT = "sheet_table_of_content"

    USER_INFO = "user_info"

    TOPICS = "topics"
    
    # Collection-specific cache types
    COLLECTIONS = "collections"
    COLLECTION_DETAIL = "collection_detail"
    