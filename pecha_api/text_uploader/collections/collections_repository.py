from typing import Any
import asyncio

import requests

from typing import Optional

from pecha_api.text_uploader.constants import APPLICATION, DestinationURL, ACCESS_TOKEN
from pecha_api.text_uploader.collections.collection_model import CollectionPayload
from pecha_api.collections.collections_repository import create_collection


async def get_collections(
    openpecha_api_url: str, languages: list[str], parent_id: str | None = None
) -> list[dict[str, Any]]:
    """
    Fetch the list of collections (categories) from the remote API for
    a list of languages.

    The remote API expects `application` and `language` as query parameters,
    e.g. `...?application=webuddhist&language=en`.

    Returns a list in the form:

    [
        {
            "language": "en",
            "collections": [ ... raw API items ... ],
        },
        {
            "language": "bo",
            "collections": [ ... raw API items ... ],
        },
    ]
    """
    all_collections: list[dict[str, Any]] = []
    categories_url = f"{openpecha_api_url}/v2/categories/"

    for language in languages:
        params = {
            "application": APPLICATION,
            "language": language,
            "parent_id": parent_id,
        }

        # `requests` is synchronous; run it in a thread so we can still await it.
        response = await asyncio.to_thread(
            requests.get,
            categories_url,
            params=params,
        )
        response.raise_for_status()

        all_collections.append(
            {
                "language": language,
                "collections": response.json(),
            }
        )

    return all_collections

async def get_collection_by_pecha_collection_id(pecha_collection_id: str, destination_url: str) -> Optional[str]:
    text_metadata_url = f"{destination_url}/text-uploader/collections/{pecha_collection_id}"
    response = await asyncio.to_thread(requests.get, text_metadata_url)
    response.raise_for_status()
    return response.json()


async def post_collections(destination_url: str, language: str, collection_model: CollectionPayload, access_token: str) -> dict[str, Any]:
    url = f"{destination_url}/collections"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    params = {"language": language}
    payload = collection_model.model_dump()

    # `requests` is synchronous; run it in a thread so we can still await it.
    response = await asyncio.to_thread(
        requests.post,
        url,
        headers=headers,
        params=params,
        json=payload,
    )

    if not response.ok:
        print(
            f"POST /collections failed "
            f"(language={language}) status={response.status_code} "
            f"body={response.text}"
        )

    return response.json()



async def upload_collection(CollectionPayload) -> dict[str, Any]:
    return await create_collection(create_collection_request=CollectionPayload)
        
