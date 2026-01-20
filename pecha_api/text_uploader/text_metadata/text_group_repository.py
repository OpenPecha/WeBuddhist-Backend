from typing import Any, List

import asyncio
import requests

from pecha_api.text_uploader.constants import OpenPechaAPIURL, DestinationURL, ACCESS_TOKEN
from pecha_api.text_uploader.text_metadata.text_metadata_model import TextGroupPayload
from pecha_api.text_uploader.text_metadata.text_metadata_model import CriticalInstanceResponse


CONTENT_TYPE = "application/json"

async def get_texts(openpecha_api_url: str, type: str | None = None, limit: int | None = None, offset: int | None = None) -> list[dict[str, Any]]:
    texts_url = f"{openpecha_api_url}/v2/texts"

    # `requests` is synchronous; run it in a thread so callers can still await.
    params = {
        "type": type,
        "limit": 100,
        "offset": 800,
    }
    response = await asyncio.to_thread(requests.get, texts_url, params=params)
    response.raise_for_status()

    return response.json()


async def get_texts_by_category(category_id: str, openpecha_api_url: str) -> list[dict[str, Any]]:
    texts_url = f"{openpecha_api_url}/v2/categories/{category_id}/texts"
    params = {
        "instance_type": 'critical',
        "limit": 100,
        "offset": 0,
    }
    response = await asyncio.to_thread(requests.get, texts_url, params=params)
    response.raise_for_status()
    return response.json()


async def get_related_texts(text_id: str, openpecha_api_url: str) -> list[dict[str, Any]]:
    related_texts_url = f"{openpecha_api_url}/v2/instances/{text_id}/related"
    response = await asyncio.to_thread(requests.get, related_texts_url)
    response.raise_for_status()
    return response.json()

async def get_text_instances(text_id: str, type: str, openpecha_api_url: str) -> list[dict[str, Any]]:
    instances_url = f"{openpecha_api_url}/v2/texts/{text_id}/instances"
    params = {
        "type": type,
    }
    response = await asyncio.to_thread(requests.get, instances_url, params=params)
    response.raise_for_status()
    return response.json()


async def post_group(type: str, destination_url: str, token: str) -> dict[str, Any]:
    """
    Create a text group in the destination (webuddhist) backend.
    """
    url = f"{destination_url}/groups"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": CONTENT_TYPE,
    }
    payload = {
        "type": type,
    }

    response = await asyncio.to_thread(
        requests.post,
        url,
        headers=headers,
        json=payload,
    )

    if not response.ok:
        # Print full details so we can see why the backend returned 4xx/5xx.
        print(
            f"POST /groups failed "
            f"(status={response.status_code}) "
            f"body={response.text}"
        )
        response.raise_for_status()

    return response.json()

async def get_critical_instances(text_id: str, openpecha_api_url: str) -> CriticalInstanceResponse:
    critical_instances_url = f"{openpecha_api_url}/v2/texts/{text_id}/instances"
    params = {"instance_type": "critical"}

    response = await asyncio.to_thread(
        requests.get,
        critical_instances_url,
        params=params,
    )
    response.raise_for_status()
    critical_instances_list = response.json()
    return CriticalInstanceResponse(critical_instances=critical_instances_list)


async def post_text(text_payload: TextGroupPayload, token: str, destination_url: str) -> dict[str, Any]:

    url = f"{destination_url}/texts"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": CONTENT_TYPE,
    }
    payload = text_payload.model_dump()

    response = await asyncio.to_thread(
        requests.post,
        url,
        headers=headers,
        json=payload,
    )

    if not response.ok:
        print(
            f"POST /texts failed "
            f"(status={response.status_code}) "
            f"body={response.text}"
        )
        response.raise_for_status()

    return response.json()


async def get_text_related_by_work(text_id: str, openpecha_api_url: str) -> list[dict[str, Any]]:
    related_texts_url = f"{openpecha_api_url}/v2/texts/{text_id}/related-by-work"
    response = await asyncio.to_thread(requests.get, related_texts_url)
    response.raise_for_status()
    data = response.json()
    return data

async def  get_text_metadata(text_id: str, openpecha_api_url: str) -> list[dict[str, Any]]:
    text_metadata_url = f"{openpecha_api_url}/v2/texts/{text_id}"
    response = await asyncio.to_thread(requests.get, text_metadata_url)
    response.raise_for_status()
    return response.json()


async def get_texts_by_pecha_text_ids(pecha_text_ids: List[str], destination_url: str) -> list[dict[str, Any]]:
    url = f"{destination_url}/text-uploader/list"
    headers = {
        "Content-Type": CONTENT_TYPE,
    }
    instance_ids = list(pecha_text_ids)
    payload = {
        "pecha_text_ids": instance_ids  
    }
    response = await asyncio.to_thread(requests.post, url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()