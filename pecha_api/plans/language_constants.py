from pecha_api.plans.plans_enums import LanguageCode

SUPPORTED_LANGUAGE_CODES = tuple(code.value for code in LanguageCode)
SUPPORTED_LANGUAGE_CODES_LABEL = ", ".join(SUPPORTED_LANGUAGE_CODES)


def language_query_description(
    purpose: str = "Language code",
    *,
    lowercase_example: bool = False,
) -> str:
    if lowercase_example:
        examples = ", ".join(f"'{code.lower()}'" for code in SUPPORTED_LANGUAGE_CODES)
        return f"{purpose} (e.g. {examples})"
    return f"{purpose} ({SUPPORTED_LANGUAGE_CODES_LABEL}). Case-insensitive."
