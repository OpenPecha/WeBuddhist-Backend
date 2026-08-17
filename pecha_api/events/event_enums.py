from enum import Enum


class RecurrenceFrequency(str, Enum):
    YEARLY = "YEARLY"
    MONTHLY = "MONTHLY"


class RecurrenceDateSystem(str, Enum):
    GREGORIAN = "GREGORIAN"
    TIBETAN_LUNAR = "TIBETAN_LUNAR"
