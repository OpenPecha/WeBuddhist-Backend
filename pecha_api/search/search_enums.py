from enum import Enum

class SearchType(Enum):
    SOURCE = "SOURCE"
    SHEET = "SHEET"

class QueryType(Enum):
    MATCH = "match"  # Full-text search (current implementation)
    TERM = "term"    # Exact term matching
    PHRASE = "phrase"  # Exact phrase matching
    WILDCARD = "wildcard"  # Pattern matching
    BOOL = "bool"    # Boolean query with exact matching

class MultilingualSearchType(Enum):
    EXACT = "exact"
    SIMILAR = "similar"
