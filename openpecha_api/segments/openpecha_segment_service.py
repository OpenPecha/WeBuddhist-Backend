from typing import Any, Dict, Optional

from pecha_api.external_clients import get_authenticated_open_pecha_client

async def fetch_related_segments(
    segment_id: str,
    limit: int = 10,
    offset: int = 0,
) -> Dict[str, Any]:

    params: Dict[str, Any] = {
        "limit": limit,
        "offset": offset,
    }
    client = get_authenticated_open_pecha_client()
    http_client = client.get_async_httpx_client()
    response = await http_client.get(
        f"/v2/segments/{segment_id}/related",
        params=params,
    )
    response.raise_for_status()
    return response.json()


async def fetch_segment_content(segment_id: str) -> Optional[str]:
    client = get_authenticated_open_pecha_client()
    http_client = client.get_async_httpx_client()
    response = await http_client.get(f"/v2/segments/{segment_id}/content")
    response.raise_for_status()
    data = response.json()
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        for key in ("content", "text", "value"):
            value = data.get(key)
            if isinstance(value, str):
                return value
    return None

async def fetch_segment_details(segment_id:str) :
    client=get_authenticated_open_pecha_client()
    http_client=client.get_async_httpx_client()
    response=await http_client.get(f"/v2/segments/{segment_id}")
    response.raise_for_status()
    return response.json()
