import re
from uuid import UUID, uuid5

from pecha_api.plans.plans_enums import LanguageCode

TRADITION_ID_NAMESPACE = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")
DEFAULT_CHAT_LANGUAGE = "en"

# Fixed onboarding paths shown in the app onboarding screen.
ONBOARDING_TRADITION_CODES: frozenset[str] = frozenset({"pali", "chinese", "tibetan"})

# Backward-compatible alias used by onboarding.
TRADITION_CODES = ONBOARDING_TRADITION_CODES

TRADITION_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,62}$")

TRADITION_REGIONS: dict[str, list[str]] = {
    "pali": [
        "Sri Lanka",
        "Thailand",
        "Myanmar",
        "Cambodia",
        "Laos",
        "Bangladesh",
        "India",
    ],
    "chinese": ["China", "Korea", "Japan", "Vietnam"],
    "tibetan": ["Tibet", "India", "Nepal", "Bhutan", "Mongolia", "Russia"],
}


def tradition_id_from_code(code: str) -> UUID:
    return uuid5(TRADITION_ID_NAMESPACE, code)


def parse_language_code(language: str | None) -> LanguageCode:
    raw = (language or DEFAULT_CHAT_LANGUAGE).strip().upper()
    try:
        return LanguageCode(raw)
    except ValueError:
        return LanguageCode.EN


def normalize_tradition_code(code: str) -> str:
    normalized = code.strip().lower().replace("-", "_").replace(" ", "_")
    if not TRADITION_CODE_PATTERN.match(normalized):
        raise ValueError(
            "tradition code must be lowercase letters/numbers/underscores, starting with a letter"
        )
    if normalized.startswith("legacy_"):
        raise ValueError("tradition code cannot start with 'legacy_'")
    return normalized


def is_managed_tradition_code(code: str | None) -> bool:
    return bool(code) and not str(code).startswith("legacy_")
