import logging
from typing import Optional, Dict, Any, List

from pecha_api.external_clients import get_authenticated_open_pecha_client

logger = logging.getLogger(__name__)


async def fetch_category_by_id(category_id: str, language: Optional[str] = None) -> Optional[Dict[str, Any]]:
    client = get_authenticated_open_pecha_client()
    http_client = client.get_async_httpx_client()
    params: Dict[str, Any] = {
        "language": language,
    }
    response = await http_client.get(f"/v2/categories/{category_id}", params=params)
    response.raise_for_status()
    return response.json()

async def fetch_categories() -> List[Dict[str, Any]]:

    client = get_authenticated_open_pecha_client()
    http_client = client.get_async_httpx_client()
    response = await http_client.get("/v2/categories")
    response.raise_for_status()
    return response.json()
