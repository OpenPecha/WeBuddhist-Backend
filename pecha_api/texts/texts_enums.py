from enum import Enum

class TextType(Enum):
    ROOT_TEXT = "root_text"
    COMMENTARY = "commentary"
    VERSION = "version"
    SHEET = "sheet"
    TRANSLATION = "translation"
    TRANSLITERATION = "transliteration"
    ADAPTATION = "adaptation"

class TextTypes(Enum):
    VERSIONS = "versions"

class SortOrder(Enum):
    ASC = "asc"
    DESC = "desc"


class SortBy(Enum):
    CREATED_DATE = "created_date"
    PUBLISHED_DATE = "published_date"


class PaginationDirection(Enum):
    NEXT = "next"
    PREVIOUS = "previous"

class TextLanguage(Enum):
    Bo = "bo"
    En = "en"
    zh = "zh"

# Language preference orders for sorting
LANGUAGE_ORDERS = {
    'bo': {'bo': 0, 'en': 1, 'zh': 2},
    'en': {'en': 0, 'bo': 1, 'zh': 2},
    'zh': {'zh': 0, 'en': 1, 'bo': 2}
}