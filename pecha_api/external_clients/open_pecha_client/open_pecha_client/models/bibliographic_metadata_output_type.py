from enum import Enum


class BibliographicMetadataOutputType(str, Enum):
    ALT_INCIPIT = "alt_incipit"
    ALT_TITLE = "alt_title"
    AUTHOR = "author"
    COLOPHON = "colophon"
    INCIPIT = "incipit"
    PERSON = "person"
    TITLE = "title"

    def __str__(self) -> str:
        return str(self.value)
