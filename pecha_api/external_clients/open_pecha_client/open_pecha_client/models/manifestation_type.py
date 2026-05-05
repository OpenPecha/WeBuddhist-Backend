from enum import Enum


class ManifestationType(str, Enum):
    COLLATED = "collated"
    CRITICAL = "critical"
    DIPLOMATIC = "diplomatic"

    def __str__(self) -> str:
        return str(self.value)
