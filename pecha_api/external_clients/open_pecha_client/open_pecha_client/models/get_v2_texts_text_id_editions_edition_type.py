from enum import Enum


class GetV2TextsTextIdEditionsEditionType(str, Enum):
    ALL = "all"
    CRITICAL = "critical"
    DIPLOMATIC = "diplomatic"

    def __str__(self) -> str:
        return str(self.value)
