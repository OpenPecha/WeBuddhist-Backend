from enum import Enum


class ContributionOutputRole(str, Enum):
    AUTHOR = "author"
    REVISER = "reviser"
    SCHOLAR = "scholar"
    TRANSLATOR = "translator"

    def __str__(self) -> str:
        return str(self.value)
