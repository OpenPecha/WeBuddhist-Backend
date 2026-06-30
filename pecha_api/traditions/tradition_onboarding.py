import json
from functools import lru_cache
from typing import Any

from fastapi import HTTPException
from starlette import status

from pecha_api.traditions.tradition_constants import (
    DEFAULT_CHAT_LANGUAGE,
    TRADITION_ONBOARDING_PATH,
)


@lru_cache(maxsize=1)
def load_tradition_onboarding() -> dict[str, Any]:
    with TRADITION_ONBOARDING_PATH.open(encoding="utf-8") as onboarding_file:
        return json.load(onboarding_file)


def get_tradition_onboarding_content(language: str = DEFAULT_CHAT_LANGUAGE) -> dict[str, Any]:
    content_by_language = load_tradition_onboarding()
    normalized_language = (language or DEFAULT_CHAT_LANGUAGE).lower()
    content = content_by_language.get(normalized_language)
    if content is None:
        content = content_by_language.get(DEFAULT_CHAT_LANGUAGE)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tradition onboarding content is not available",
        )
    return content


def list_tradition_path_codes() -> frozenset[str]:
    english_content = load_tradition_onboarding()["en"]
    return frozenset(english_content["paths"].keys())


def get_tradition_path_entry(
    code: str,
    language: str = DEFAULT_CHAT_LANGUAGE,
) -> dict[str, str] | None:
    content_by_language = load_tradition_onboarding()
    normalized_language = (language or DEFAULT_CHAT_LANGUAGE).lower()
    content = content_by_language.get(normalized_language) or content_by_language.get(
        DEFAULT_CHAT_LANGUAGE
    )
    if content is None:
        return None
    path_entry = content.get("paths", {}).get(code)
    if not isinstance(path_entry, dict):
        return None
    return path_entry
