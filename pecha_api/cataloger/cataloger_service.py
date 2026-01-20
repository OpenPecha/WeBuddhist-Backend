from typing import Optional
import httpx
import asyncio
from pecha_api.cataloger.cataloger_response_model import (
    CatalogedTextsDetailsResponse,
    CatalogedTextsResponse,
    CatalogedTexts,
    ExternalPechaTextResponse,
    ExternalPechaInstanceRelatedResponse,
    Relation,
    Metadata
)
from pecha_api.http_message_utils import handle_http_status_error, handle_request_error
from ..config import get
from pecha_api.constants import Constants


client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))

ACCEPT_JSON_HEADER = {"Accept": "application/json"}
EXTERNAL_PECHA_API_URL = get("EXTERNAL_PECHA_API_URL")

async def get_cataloged_texts(
    search: Optional[str],
    skip: int,
    limit: int,
) -> CatalogedTextsResponse:
    data = await call_external_pecha_api_cataloged_texts(search=search, skip=skip, limit=limit)

    texts = [
        CatalogedTexts(
            text_id=item["id"],
            title=ensure_dict(item.get("title")),
            language=item["language"],
            type=item["type"],
            status=False,
        )
        for item in (data or [])
    ]

    return CatalogedTextsResponse(texts=texts)

async def get_cataloged_texts_details(text_id: str) -> CatalogedTextsDetailsResponse | None:
    if text_id is None:
        return None
    
    text_details, instance_ids = await asyncio.gather(
        call_external_pecha_api_texts(text_id),
        call_external_pecha_api_instances(text_id)
    )
    
    all_related_instances = []
    if instance_ids:
        for instance_id in instance_ids:
            related = await call_external_pecha_api_related_instances(instance_id)
            all_related_instances.extend(related)


    relations = []
    for related_instance in all_related_instances:
        metadata = Metadata(
            text_id=related_instance.text_id,
            title=ensure_dict(related_instance.title),
            language=related_instance.language
        )
        relation = Relation(
            relation_type=related_instance.relation_type,
            status=False,
            metadata=metadata
        )
        relations.append(relation)
    
    return CatalogedTextsDetailsResponse(
        title=ensure_dict(text_details.title),
        category_id=text_details.category_id,
        status=False,
        relations=relations
    )

async def call_external_pecha_api_texts(
    text_id: str
) -> ExternalPechaTextResponse:

    endpoint = f"{EXTERNAL_PECHA_API_URL}/texts/{text_id}"    
    try:
        response = await client.get(endpoint, headers=ACCEPT_JSON_HEADER)
        response.raise_for_status()
        data = response.json()
        return ExternalPechaTextResponse(**data)
            
    except httpx.HTTPStatusError as e:
        handle_http_status_error(e)
    except httpx.RequestError as e:
        handle_request_error(e)

async def call_external_pecha_api_instances(
    text_id: str
) -> list[str]:
    endpoint = f"{EXTERNAL_PECHA_API_URL}/texts/{text_id}/instances?instance_type={Constants.INSTANCE_TYPE}"   
    try:
        response = await client.get(endpoint, headers=ACCEPT_JSON_HEADER)
        response.raise_for_status()
        data = response.json()
        return [item["id"] for item in data if "id" in item]
            
    except httpx.HTTPStatusError as e:
        handle_http_status_error(e)
    except httpx.RequestError as e:
        handle_request_error(e)

async def call_external_pecha_api_related_instances(
    id: str
) -> list[ExternalPechaInstanceRelatedResponse]:
    endpoint = f"{EXTERNAL_PECHA_API_URL}/instances/{id}/related"   
    try:
        response = await client.get(endpoint, headers=ACCEPT_JSON_HEADER)
        response.raise_for_status()
        data = response.json()
        
        related_instances = []
        for item in data:
            metadata = item.get("metadata", {})
            related_instance = ExternalPechaInstanceRelatedResponse(
                title=metadata.get("title", {}),
                text_id=metadata.get("text_id", ""),
                language=metadata.get("language", ""),
                relation_type=item.get("relationship", "")
            )
            related_instances.append(related_instance)
        
        return related_instances
                    
    except httpx.HTTPStatusError as e:
        handle_http_status_error(e)
    except httpx.RequestError as e:
        handle_request_error(e)

async def call_external_pecha_api_cataloged_texts(
    search: Optional[str],
    skip: int,
    limit: int,
) -> list[dict]:
    params = {"offset": skip, "limit": limit}
    if search:
        params["title"] = search
    endpoint = f"{EXTERNAL_PECHA_API_URL}/texts"   
    try:
        response = await client.get(
            endpoint,
            headers=ACCEPT_JSON_HEADER,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        handle_http_status_error(e)
    except httpx.RequestError as e:
        handle_request_error(e)


def ensure_dict(value) -> dict:
    """Return value if it's a dict, otherwise return an empty dict."""
    return value if isinstance(value, dict) else {}
