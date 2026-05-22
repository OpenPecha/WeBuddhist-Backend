import logging
from typing import Optional, Dict, Any

from pecha_api.external_clients import get_authenticated_open_pecha_client

logger = logging.getLogger(__name__)


async def fetch_category_by_id(category_id: str) -> Optional[Dict[str, Any]]:
    client = get_authenticated_open_pecha_client()
    http_client = client.get_async_httpx_client()
    response = await http_client.get(f"/v2/categories/{category_id}")
    response.raise_for_status()
    return response.json()
