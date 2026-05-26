from typing import Dict, List, Optional

import httpx
from fastapi import HTTPException
from starlette import status

from pecha_api.error_contants import ErrorConstants
from pecha_api.http_message_utils import handle_http_status_error, handle_request_error
from pecha_api.plans.response_message import (
    EXTERNAL_PECHA_API_URL_NOT_CONFIGURED,
    TITLE_OR_AUTHOR_QUERY_REQUIRED,
)
from pecha_api.config import get
from .texts_repository import get_texts_by_titles
from .texts_response_models import TitleSearchResult

EXTERNAL_TITLE_SEARCH_API_URL = get("EXTERNAL_TITLE_SEARCH_API_URL")
ACCEPT_JSON_HEADER = {"Accept": "application/json"}


def extract_title_for_language(title_payload: object, language: Optional[str]) -> Optional[str]:
    if isinstance(title_payload, dict):
        if language and isinstance(title_payload.get(language), str):
            return title_payload.get(language)
        for value in title_payload.values():
            if isinstance(value, str) and value.strip():
                return value
        return None
    if isinstance(title_payload, str):
        return title_payload.strip() or None
    return None


async def get_titles_and_ids_by_query(
    title: Optional[str],
    author: Optional[str],
    limit: int,
    offset: int,
) -> List[TitleSearchResult]:
    if not title and not author:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=TITLE_OR_AUTHOR_QUERY_REQUIRED,
        )
    if not EXTERNAL_TITLE_SEARCH_API_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=EXTERNAL_PECHA_API_URL_NOT_CONFIGURED,
        )

    params: Dict[str, object] = {"limit": limit, "offset": offset}
    if title:
        params["title"] = title
    if author:
        params["author"] = author

    endpoint = f"{EXTERNAL_TITLE_SEARCH_API_URL}/v2/texts"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.get(endpoint, headers=ACCEPT_JSON_HEADER, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as e:
        handle_http_status_error(e)
    except httpx.RequestError as e:
        handle_request_error(e)

    titles = []
    for item in data or []:
        if not isinstance(item, dict):
            continue
        language = item.get("language")
        title_value = extract_title_for_language(item.get("title"), language)
        if title_value:
            titles.append(title_value)

    unique_titles = list(dict.fromkeys(titles))
    if not unique_titles:
        return []

    texts = await get_texts_by_titles(titles=unique_titles)
    return [TitleSearchResult(id=str(text.id), title=text.title) for text in texts]
