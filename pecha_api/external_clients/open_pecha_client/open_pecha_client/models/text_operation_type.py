from enum import Enum


class TextOperationType(str, Enum):
    DELETE = "delete"
    INSERT = "insert"
    REPLACE = "replace"

    def __str__(self) -> str:
        return str(self.value)
