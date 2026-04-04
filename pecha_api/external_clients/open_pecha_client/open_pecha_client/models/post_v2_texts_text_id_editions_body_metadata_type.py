from enum import Enum


class PostV2TextsTextIdEditionsBodyMetadataType(str, Enum):
    CRITICAL = "critical"
    DIPLOMATIC = "diplomatic"

    def __str__(self) -> str:
        return str(self.value)
