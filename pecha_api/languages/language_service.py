import json
from functools import lru_cache
from typing import Any

from fastapi import HTTPException
from starlette import status

from pecha_api.languages.language_constants import LANGUAGES_JSON_PATH
from pecha_api.languages.language_response_models import LanguageDTO, LanguageListResponse


@lru_cache(maxsize=1)
def load_languages() -> dict[str, Any]:
    if not LANGUAGES_JSON_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Languages configuration is not available",
        )
    with LANGUAGES_JSON_PATH.open(encoding="utf-8") as languages_file:
        return json.load(languages_file)


def list_languages_service(*, enabled_only: bool = True) -> LanguageListResponse:
    payload = load_languages()
    languages = [
        LanguageDTO(
            code=entry["code"],
            name=entry["name"],
            native_name=entry["native_name"],
            enabled=entry.get("enabled", True),
        )
        for entry in payload.get("languages", [])
        if not enabled_only or entry.get("enabled", True)
    ]
    return LanguageListResponse(languages=languages)
