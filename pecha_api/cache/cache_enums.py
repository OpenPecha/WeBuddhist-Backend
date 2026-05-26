from enum import Enum

class CacheType(Enum):
    TEXT_DETAIL = "text_detail"
    TEXT_VERSIONS = "text_versions"
    TEXTS_BY_ID_OR_COLLECTION = "texts_by_id_or_collection"
    TEXT_TABLE_OF_CONTENTS = "text_table_of_contents"
    DETAIL_TEXT_TABLE_OF_CONTENT = "detail_text_table_of_content"

    SEGMENTS_DETAILS = "segments_details"

    GROUP_DETAIL = "group_detail"

    USER_INFO = "user_info"

    TOPICS = "topics"
    
    # Collection-specific cache types
    COLLECTIONS = "collections"
    COLLECTION_DETAIL = "collection_detail"
    