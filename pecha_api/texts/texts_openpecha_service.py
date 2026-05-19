import logging
from typing import Optional, Dict, Any, List

from fastapi import HTTPException
from starlette import status

from pecha_api.config import get
from pecha_api.texts.texts_enums import LANGUAGE_ORDERS
from pecha_api.texts.texts_response_models import TextDTO, TextsCategoryResponse
from pecha_api.collections.collections_response_models import CollectionModel
from openpecha_api.text.openpecha_text_service import fetch_texts_by_category, fetch_text_by_id

logger = logging.getLogger(__name__)

DEFAULT_LANGUAGE = get("DEFAULT_LANGUAGE") or "en"
LANGUAGE_PRIORITY_LIST = ["en", "bo", "zh"]


def _get_language_priority_order(selected_language: str) -> List[str]:
    order_map = LANGUAGE_ORDERS.get(selected_language, LANGUAGE_ORDERS.get("en", {}))
    sorted_langs = sorted(order_map.keys(), key=lambda lang: order_map[lang])
    return sorted_langs


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


def _map_external_text_to_dto(item: Dict[str, Any], language: Optional[str] = None) -> TextDTO:
    title = _extract_title(item.get("title", {}), language)
    date_value = item.get("date") or ""

    return TextDTO(
        id=item.get("id", ""),
        pecha_text_id=item.get("bdrc") or item.get("id", ""),
        title=title,
        language=item.get("language") or "",
        group_id=item.get("category_id") or "",
        type="root_text",
        summary="",
        is_published=True,
        created_date=date_value,
        updated_date=date_value,
        published_date=date_value,
        published_by="",
        categories=[item.get("category_id")] if item.get("category_id") else [],
        views=0,
        likes=[],
        source_link=None,
        ranking=None,
        license=item.get("license"),
    )


async def get_texts_by_collection_from_openpecha(
    collection_id: str,
    language: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
) -> TextsCategoryResponse:
    if not language:
        language = DEFAULT_LANGUAGE

    priority_languages = _get_language_priority_order(language)
    collected_texts: List[TextDTO] = []
    remaining = limit

    for lang in priority_languages:
        if remaining <= 0:
            break

        try:
            data = await fetch_texts_by_category(
                category_id=collection_id,
                language=lang,
                limit=remaining,
                offset=skip if lang == language else 0,
            )
        except Exception as e:
            logger.error(f"Failed to fetch texts for language={lang}, category={collection_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to fetch texts from upstream service",
            )

        items = data.get("items", [])
        for item in items:
            if remaining <= 0:
                break
            collected_texts.append(_map_external_text_to_dto(item, lang))
            remaining -= 1

    collection = CollectionModel(
        id=collection_id,
        pecha_collection_id=collection_id,
        title="",
        description="",
        language=language,
        slug=collection_id,
        has_child=False,
    )

    return TextsCategoryResponse(
        collection=collection,
        texts=collected_texts,
        total=len(collected_texts),
        skip=skip,
        limit=limit,
    )


async def get_text_by_id_from_openpecha(text_id: str) -> TextDTO:
    try:
        data = await fetch_text_by_id(text_id)
    except Exception as e:
        logger.error(f"Failed to fetch text {text_id}: {e}")
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
