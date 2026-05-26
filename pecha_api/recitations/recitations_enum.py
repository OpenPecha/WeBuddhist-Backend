import enum

class RecitationListTextType(enum.Enum):
    RECITATIONS = "recitations"
    TRANSLATIONS = "translations"
    TRANSLITERATIONS = "transliterations"
    ADAPTATIONS = "adaptations"
    
class LanguageCode(enum.Enum):
    BO = "bo"
