from enum import Enum


class LicenseType(str, Enum):
    CC0 = "cc0"
    CC_BY = "cc-by"
    CC_BY_NC = "cc-by-nc"
    CC_BY_NC_ND = "cc-by-nc-nd"
    CC_BY_NC_SA = "cc-by-nc-sa"
    CC_BY_ND = "cc-by-nd"
    CC_BY_SA = "cc-by-sa"
    COPYRIGHTED = "copyrighted"
    PUBLIC = "public"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return str(self.value)
