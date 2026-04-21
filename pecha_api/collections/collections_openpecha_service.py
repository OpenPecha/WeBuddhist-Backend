import logging
from typing import Optional, List

from fastapi import HTTPException
from starlette import status

from pecha_api.external_clients import get_authenticated_open_pecha_client
from pecha_api.external_clients.open_pecha_client.open_pecha_client.api.categories import get_v2_categories
from pecha_api.external_clients.open_pecha_client.open_pecha_client.models.category_output import CategoryOutput
from pecha_api.external_clients.open_pecha_client.open_pecha_client.models.get_v2_categories_response_400 import GetV2CategoriesResponse400
from pecha_api.external_clients.open_pecha_client.open_pecha_client.models.get_v2_categories_response_500 import GetV2CategoriesResponse500
from pecha_api.external_clients.open_pecha_client.open_pecha_client.types import UNSET
from .collections_response_models import CollectionModel, CollectionsResponse, Pagination
from pecha_api.config import get

logger = logging.getLogger(__name__)



def _extract_title(category: CategoryOutput, language: str) -> str:
    title_dict = category.title.to_dict() if hasattr(category.title, 'to_dict') else {}
    return title_dict.get(language, title_dict.get('en', ''))


def _extract_description(category: CategoryOutput, language: str) -> str:
    if category.description is None or isinstance(category.description, type(UNSET)):
        return ""
    desc_dict = category.description.to_dict() if hasattr(category.description, 'to_dict') else {}
    return desc_dict.get(language, desc_dict.get('en', '')) or ""


def _category_to_collection_model(category: CategoryOutput, language: str) -> CollectionModel:
    title = _extract_title(category, language)
    return CollectionModel(
        id=category.id,
        pecha_collection_id=category.id,
        title=title,
        description=_extract_description(category, language),
        has_child=len(category.children) > 0 if category.children else False,
        language=language,
        slug=title or category.id
    )


async def get_collections_from_openpecha(
    language: Optional[str],
    parent_id: Optional[str],
    skip: int,
    limit: int
) -> CollectionsResponse:
    if language is None:
        language = get("DEFAULT_LANGUAGE") or "en"

    client = get_authenticated_open_pecha_client()
    
    parent_id_param = parent_id if parent_id else UNSET
    
    try:
        response = await get_v2_categories.asyncio(
            client=client,
            parent_id=parent_id_param,
            language=language,
            x_application=get("APPLICATION")
        )
    except Exception as e:
        logger.error(
            f"Failed to fetch categories from OpenPecha API: {e} | "
            f"URL: {client._base_url}/v2/categories | "
            f"Headers:{client._headers} | "
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch collections from upstream service"
        )
    
    if isinstance(response, GetV2CategoriesResponse400):
        logger.error(f"OpenPecha API returned 400: {response.error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.error
        )
    
    if isinstance(response, GetV2CategoriesResponse500):
        logger.error(f"OpenPecha API returned 500: {response.error}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream service error"
        )
    
    categories: List[CategoryOutput] = response if response else []
    
    collection_list = [
        _category_to_collection_model(category, language)
        for category in categories
    ]
    
    total = len(collection_list)
    paginated_collections = collection_list[skip:skip + limit]
    
    parent_collection = await get_collection_by_id(collection_id=parent_id, language=language) if parent_id else None
    
    pagination = Pagination(total=total, skip=skip, limit=limit)
    
    return CollectionsResponse(
        parent=parent_collection,
        pagination=pagination,
        collections=paginated_collections
    )

async def get_collection_by_id(collection_id: str, language: str) -> Optional[CollectionModel]:
    client = get_authenticated_open_pecha_client()
    selected_collection = None
    if collection_id:
        try:
            logger.debug(
                f"Calling OpenPecha API: {client.base_url}/v2/categories | "
                f"Headers: X-API-Key=***, X-Application={get('APPLICATION')} | "
                f"Params: parent_id=UNSET, language={language}"
            )
            response = await get_v2_categories.asyncio(
                client=client,
                parent_id=UNSET,
                language=language,
                x_application=get("APPLICATION")
            )
        except Exception as e:
            logger.error(
                f"Failed to fetch collection by id from OpenPecha API: {e} | "
                f"URL: {client.base_url}/v2/categories | "
                f"Headers: X-API-Key=***, X-Application={get('APPLICATION')} | "
                f"Params: parent_id=UNSET, language={language}"
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to fetch collection from upstream service"
            )
        
        if isinstance(response, GetV2CategoriesResponse400):
            logger.error(f"OpenPecha API returned 400: {response.error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.error
            )
        
        if isinstance(response, GetV2CategoriesResponse500):
            logger.error(f"OpenPecha API returned 500: {response.error}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Upstream service error"
            )
        
        categories = response if response else []
        if categories and isinstance(categories, list):
            for cat in categories:
                if cat.id == collection_id:
                    selected_collection = _category_to_collection_model(cat, language)
                    break
    return selected_collection

