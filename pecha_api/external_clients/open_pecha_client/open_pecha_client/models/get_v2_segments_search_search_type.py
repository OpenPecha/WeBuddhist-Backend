from enum import Enum


class GetV2SegmentsSearchSearchType(str, Enum):
    BM25 = "bm25"
    EXACT = "exact"
    HYBRID = "hybrid"
    SEMANTIC = "semantic"

    def __str__(self) -> str:
        return str(self.value)
