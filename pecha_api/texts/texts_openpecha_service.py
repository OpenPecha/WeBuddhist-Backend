import logging
import httpx
from typing import Optional, Dict, Any, List

from fastapi import HTTPException
from starlette import status

from pecha_api.config import get
from pecha_api.texts.texts_enums import LANGUAGE_ORDERS
from pecha_api.texts.texts_response_models import TextDTO, TextsCategoryResponse, TextVersionResponse, TextVersion
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


def map_external_text_to_dto(item: Dict[str, Any], language: Optional[str] = None) -> TextDTO:
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
            collected_texts.append(map_external_text_to_dto(item, lang))
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

    return map_external_text_to_dto(data, data.get("language"))


async def fetch_text_from_external_api(text_id: str) -> Dict[str, Any]:
    endpoint = f"{get('EXTERNAL_DEV_PECHA_API_URL')}/v2/texts/{text_id}"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.get(endpoint, headers={"Accept": "application/json"})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching text {text_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch text from external API: {e.response.status_code}",
        )
    except httpx.RequestError as e:
        logger.error(f"Request error fetching text {text_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to connect to external API",
        )


async def fetch_translation_details(translation_ids: List[str]) -> List[Dict[str, Any]]:
    translation_details = []
    for translation_id in translation_ids:
        try:
            data = await fetch_text_from_external_api(translation_id)
            if data:
                translation_details.append(data)
        except HTTPException as e:
            logger.warning(f"Failed to fetch translation {translation_id}: {e.detail}")
            continue
    return translation_details


def map_external_text_to_text_version(item: Dict[str, Any], language: Optional[str] = None) -> TextVersion:
    title = _extract_title(item.get("title", {}), language)
    date_value = item.get("date") or ""
    
    return TextVersion(
        id=item.get("id", ""),
        title=title,
        parent_id=item.get("translation_of") or item.get("commentary_of"),
        priority=None,
        language=item.get("language") or "",
        type="translation",
        group_id=item.get("category_id") or "",
        table_of_contents=[],
        is_published=True,
        created_date=date_value,
        updated_date=date_value,
        published_date=date_value,
        published_by="",
        source_link=None,
        ranking=None,
        license=item.get("license"),
    )


def filter_versions_by_language(
    versions: List[TextVersion], 
    language: Optional[str]
) -> List[TextVersion]:
    if not language:
        return versions
    return [v for v in versions if v.language == language]


def paginate_versions(
    versions: List[TextVersion], 
    skip: int, 
    limit: int
) -> List[TextVersion]:
    return versions[skip:skip + limit]


async def get_text_versions_from_openpecha(
    text_id: str,
    language: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
) -> TextVersionResponse:

    text_data = await fetch_text_from_external_api(text_id)
    
    if not text_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Text with id '{text_id}' not found",
        )
    
    root_text = map_external_text_to_dto(text_data, text_data.get("language"))
    
    translation_ids = text_data.get("translations", [])
    
    if not translation_ids:
        return TextVersionResponse(
            text=root_text,
            versions=[]
        )
    
    translation_details = await fetch_translation_details(translation_ids)
    
    versions = [
        map_external_text_to_text_version(item, item.get("language"))
        for item in translation_details
    ]
    
    filtered_versions = filter_versions_by_language(versions, language)
    
    paginated_versions = paginate_versions(filtered_versions, skip, limit)
    
    return TextVersionResponse(
        text=root_text,
        versions=paginated_versions
    )


async def fetch_commentary_details(commentary_ids: List[str]) -> List[Dict[str, Any]]:
    commentary_details = []
    for commentary_id in commentary_ids:
        try:
            data = await fetch_text_from_external_api(commentary_id)
            if data:
                commentary_details.append(data)
        except HTTPException as e:
            logger.warning(f"Failed to fetch commentary {commentary_id}: {e.detail}")
            continue
    return commentary_details


async def get_text_commentaries_from_openpecha(
    text_id: str,
    skip: int = 0,
    limit: int = 10
) -> List[TextDTO]:

    text_data = await fetch_text_from_external_api(text_id)
    
    if not text_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Text with id '{text_id}' not found",
        )
    
    commentary_ids = text_data.get("commentaries", [])
    
    if not commentary_ids:
        return []
    
    commentary_details = await fetch_commentary_details(commentary_ids)
    
    commentaries = [
        map_external_text_to_dto(item, item.get("language"))
        for item in commentary_details
    ]
    
    paginated_commentaries = commentaries[skip:skip + limit]
    
    return paginated_commentaries
