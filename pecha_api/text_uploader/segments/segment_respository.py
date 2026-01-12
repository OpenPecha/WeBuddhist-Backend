from typing import Any, List

import asyncio
import requests


async def get_segments_annotation(pecha_text_id: str, openpecha_api_url: str) -> list[dict[str, Any]]:
    """
    Fetch the list of segment annotations for a given Pecha text (instance).
    """
    instances_url = f"{openpecha_api_url}/v2/instances/{pecha_text_id}"
    params = {
        "annotation": "true",
        "content": "true"
        }

    # `requests` is synchronous; run it in a thread so callers can still await.
    response = await asyncio.to_thread(
        requests.get,
        instances_url,
        params=params,
    )
    response.raise_for_status()

    # The API is expected to return JSON, usually a list of instances/segments.
    return response.json()

async def get_segments_id_by_annotation_id(annotation_id: str, openpecha_api_url: str) -> list[dict[str, Any]]:
    url = f"{openpecha_api_url}/v2/annotations/{annotation_id}"
    response = await asyncio.to_thread(requests.get, url)
    response.raise_for_status()
    return response.json()

async def get_segments_by_id(annotation_id: str, openpecha_api_url: str) -> dict[str, Any]:
    """
    Fetch a single segmentation annotation by its ID.
    """
    url = (
        f"{openpecha_api_url}/v2/annotations/{annotation_id}"
    )

    response = await asyncio.to_thread(
        requests.get,
        url,
    )
    response.raise_for_status()

    return response.json()


async def get_segment_content(
    segment_id: List[str], pecha_text_id: str, openpecha_api_url: str
) -> list[dict[str, Any]]:

    url = (
        f"{openpecha_api_url}"
        f"/v2/instances/{pecha_text_id}/segment-content"
    )
    payload = {
        "segment_ids": segment_id
    }

    try:
        response = await asyncio.to_thread(
            requests.post,
            url,
            json=payload,
            timeout=100000,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error in get_segment_content: {e}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        raise
    except requests.exceptions.RequestException as e:
        print(f"Request Error in get_segment_content: {e}")
        raise
    except Exception as e:
        print(f"Unexpected Error in get_segment_content: {e}")
        raise


async def post_segments(
    segments_payload: dict[str, Any],
    destination_url: str,
    token: str,
) -> dict[str, Any]:

    url = f"{destination_url}/segments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    # payload: dict[str, Any] = {
    #     "text_id": segments_payload["text_id"],
    #     "segments": segments_payload["segments"],
    # }

    response = await asyncio.to_thread(
        requests.post,
        url,
        headers=headers,
        json=segments_payload,
    )

    if not response.ok:
        print(
            "POST /segments failed"
            f"(text_id={segments_payload['text_id']}) status={response.status_code} "
            f"body={response.text}"
        )
        response.raise_for_status()

    return response.json()



async def get_segments_by_id(annotation_id: str, openpecha_api_url: str) -> dict[str, Any]:
    """
    Fetch a single segmentation annotation by its ID.
    """
    url = (
        f"{openpecha_api_url}/v2/annotations/{annotation_id}"
    )

    response = await asyncio.to_thread(
        requests.get,
        url,
    )
    response.raise_for_status()

    return response.json()

