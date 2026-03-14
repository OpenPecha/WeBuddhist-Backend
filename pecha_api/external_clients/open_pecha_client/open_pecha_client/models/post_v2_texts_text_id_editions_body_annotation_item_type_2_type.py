from enum import Enum


class PostV2TextsTextIdEditionsBodyAnnotationItemType2Type(str, Enum):
    AUTHOR = "author"
    COLOPHON = "colophon"
    INCIPIT_TITLE = "incipit_title"
    TITLE = "title"

    def __str__(self) -> str:
        return str(self.value)
