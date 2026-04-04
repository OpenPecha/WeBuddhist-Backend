from enum import Enum


class GetV2EditionsEditionIdAnnotationsTypeItem(str, Enum):
    ALIGNMENT = "alignment"
    BIBLIOGRAPHY = "bibliography"
    DURCHEN = "durchen"
    PAGINATION = "pagination"
    SEGMENTATION = "segmentation"

    def __str__(self) -> str:
        return str(self.value)
