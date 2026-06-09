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
    HYBRID = "hybrid"      # Combined semantic + keyword search
    BM25 = "bm25"         # Keyword-based ranking algorithm
    SEMANTIC = "semantic" # Vector similarity search
    EXACT = "exact"       # Exact text matching

class V2ContentSearchType(Enum):
    EXACT = "exact"
    SIMILAR = "similar"
