from typing import Any
import asyncio
import requests

async def post_toc(toc_payload: dict[str, Any], destination_url: str, token: str):
    url = f"{destination_url}/texts/table-of-content"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    response = await asyncio.to_thread(requests.post, url, headers=headers, json=toc_payload)
    response.raise_for_status()
    return response.json()