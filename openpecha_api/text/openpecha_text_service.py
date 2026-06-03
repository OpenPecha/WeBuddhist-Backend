import logging
from typing import Optional, Dict, Any

from pecha_api.external_clients import get_authenticated_open_pecha_client

logger = logging.getLogger(__name__)


async def fetch_texts_by_category(
    category_id: str,
    language: Optional[str] = None,
    title: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "category_id": category_id,
        "limit": limit,
        "offset": offset,
    }
    if language:
        params["language"] = language
    if title:
        params["title"] = title

    client = get_authenticated_open_pecha_client()
    http_client = client.get_async_httpx_client()
    response = await http_client.get("/v2/texts", params=params)
    response.raise_for_status()
    return response.json()


async def fetch_text_by_id(text_id: str) -> Optional[Dict[str, Any]]:
    client = get_authenticated_open_pecha_client()
    http_client = client.get_async_httpx_client()
    response = await http_client.get(f"/v2/texts/{text_id}")
    response.raise_for_status()
    return response.json()
