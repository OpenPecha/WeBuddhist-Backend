import json
import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from starlette import status

from openpecha_api.text.openpecha_text_service import fetch_texts_by_category
from pecha_api.cache.cache_enums import CacheType
from pecha_api.cache.cache_repository import get_cache_data, set_cache
from pecha_api.config import get as get_config, get_int as get_config_int
from pecha_api.languages.language_constants import LANGUAGES_JSON_PATH
from pecha_api.languages.language_response_models import LanguageDTO, LanguageListResponse
from pecha_api.utils import Utils

logger = logging.getLogger(__name__)

# OpenPecha's /v2/texts caps `limit` at 100
RECITATION_CATEGORY_TEXTS_FETCH_LIMIT = 100


@lru_cache(maxsize=1)
def load_languages() -> dict[str, Any]:
    if not LANGUAGES_JSON_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Languages configuration is not available",
        )
    with LANGUAGES_JSON_PATH.open(encoding="utf-8") as languages_file:
        return json.load(languages_file)


async def _fetch_recitation_language_codes(category_id: str) -> List[str]:
    """Page through every text in the recitation category and collect its distinct language codes."""
    hashed_key = Utils.generate_hash_key(payload=[category_id, CacheType.RECITATION_LANGUAGES.value])
    cached_codes = await get_cache_data(hash_key=hashed_key)
    if cached_codes is not None:
        return cached_codes

    language_codes: List[str] = []
    seen: set[str] = set()
    offset = 0
    while True:
        try:
            page = await fetch_texts_by_category(
                category_id=category_id,
                limit=RECITATION_CATEGORY_TEXTS_FETCH_LIMIT,
                offset=offset,
            )
        except Exception:
            logger.exception("Failed to fetch recitation texts from OpenPecha category %s", category_id)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to fetch recitation languages from upstream service",
            )

        items = page.get("items", [])
        for item in items:
            language = item.get("language")
            if language and language not in seen:
                seen.add(language)
                language_codes.append(language)

        if not page.get("has_more") or not items:
            break
        offset += len(items)

    await set_cache(
        hash_key=hashed_key,
        value=language_codes,
        cache_time_out=get_config_int("CACHE_COLLECTION_TIMEOUT"),
    )
    return language_codes


def _build_language_dto(code: str, entry: Optional[Dict[str, Any]]) -> LanguageDTO:
    if entry is not None:
        return LanguageDTO(
            code=entry["code"],
            name=entry["name"],
            native_name=entry["native_name"],
            enabled=entry.get("enabled", True),
        )
    logger.warning("Recitation language code '%s' has no entry in languages.json", code)
    return LanguageDTO(code=code, name=code, native_name=code, enabled=True)


async def list_languages_service(
    *, enabled_only: bool = True, recitation_only: bool = False
) -> LanguageListResponse:
    payload = load_languages()

    if recitation_only:
        language_codes = await _fetch_recitation_language_codes(
            category_id=get_config("RECITATION_CATEGORY_ID")
        )
        entries_by_code = {entry["code"]: entry for entry in payload.get("languages", [])}
        languages = [
            _build_language_dto(code, entries_by_code.get(code))
            for code in language_codes
        ]
        return LanguageListResponse(languages=languages)

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
