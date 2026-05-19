from typing import Optional, Dict, Any, List, Tuple

from fastapi import HTTPException
from starlette import status

from pecha_api.config import get
from pecha_api.texts.texts_enums import LANGUAGE_ORDERS
from pecha_api.texts.texts_response_models import V2TextDTO, V2TextsCategoryResponse
from pecha_api.collections.collections_response_models import V2CollectionModel
from openpecha_api.text.openpecha_text_service import fetch_texts_by_category, fetch_text_by_id
from openpecha_api.collection.openpecha_collection_service import fetch_category_by_id


def _extract_title(title_payload: Any, language: Optional[str] = None) -> str:
    if isinstance(title_payload, dict):
        if language and language in title_payload:
            return title_payload[language]
        for val in title_payload.values():
            if isinstance(val, str) and val.strip():
                return val
        return ""
    if isinstance(title_payload, str):
        return title_payload.strip()
    return ""


def _map_external_text_to_dto(item: Dict[str, Any], language: Optional[str] = None) -> V2TextDTO:
    title = _extract_title(item.get("title", {}), language)

    return V2TextDTO(
        id=item.get("id", ""),
        title=title,
        language=item.get("language") or "",
        license=item.get("license"),
    )


def _languages_in_priority_order(language: str) -> List[str]:
    priority_map = LANGUAGE_ORDERS.get(language) or LANGUAGE_ORDERS["en"]
    return sorted(priority_map.keys(), key=lambda lang: priority_map[lang])


async def _fetch_language_page(
    collection_id: str,
    language: str,
    offset: int,
    limit: int,
) -> Dict[str, Any]:
    try:
        return await fetch_texts_by_category(
            category_id=collection_id,
            language=language,
            offset=offset,
            limit=limit,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch texts from upstream service",
        )


async def _get_texts_by_collection_id(
    collection_id: str,
    language: str,
    skip: int,
    limit: int,
) -> Tuple[List[V2TextDTO], int]:
    languages = _languages_in_priority_order(language)

    remaining_skip = skip
    remaining_limit = limit
    grand_total = 0
    collected: List[V2TextDTO] = []

    for lang in languages:
        if remaining_limit > 0:
            page = await _fetch_language_page(
                collection_id=collection_id,
                language=lang,
                offset=remaining_skip,
                limit=remaining_limit,
            )
        else:
            page = await _fetch_language_page(
                collection_id=collection_id,
                language=lang,
                offset=0,
                limit=1,
            )

        lang_total = int(page.get("total", 0))
        grand_total += lang_total

        if remaining_limit == 0:
            continue

        if lang_total <= remaining_skip:
            remaining_skip -= lang_total
            continue

        items = page.get("items", [])
        collected.extend(_map_external_text_to_dto(item, lang) for item in items)
        remaining_skip = 0
        remaining_limit -= len(items)

    return collected, grand_total


async def get_texts_by_collection_from_openpecha(
    collection_id: str,
    language: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
) -> V2TextsCategoryResponse:
    if not language:
        language = get("DEFAULT_LANGUAGE")

    texts, total = await _get_texts_by_collection_id(
        collection_id=collection_id,
        language=language,
        skip=skip,
        limit=limit,
    )

    category_title = ""
    try:
        category_data = await fetch_category_by_id(collection_id)
        if category_data:
            category_title = _extract_title(category_data.get("title", {}), language)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch category title from upstream service",
        )

    collection = V2CollectionModel(
        id=collection_id,
        title=category_title,
        language=language,
    )

    return V2TextsCategoryResponse(
        collection=collection,
        texts=texts,
        total=total,
        skip=skip,
        limit=limit,
    )


async def get_text_by_id_from_openpecha(text_id: str) -> V2TextDTO:
    try:
        data = await fetch_text_by_id(text_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch text from upstream service",
        )

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Text with id '{text_id}' not found",
        )

    return _map_external_text_to_dto(data, data.get("language"))
