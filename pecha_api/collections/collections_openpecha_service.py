from typing import Optional, List

from pecha_api.external_clients import get_open_pecha_client
from pecha_api.external_clients.open_pecha_client.open_pecha_client.api.categories import get_v2_categories
from pecha_api.external_clients.open_pecha_client.open_pecha_client.models.category_output import CategoryOutput
from pecha_api.external_clients.open_pecha_client.open_pecha_client.types import UNSET
from .collections_response_models import CollectionModel, CollectionsResponse, Pagination
from pecha_api.config import get

X_APPLICATION = "webuddhist"


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
    language: str,
    parent_id: Optional[str],
    skip: int,
    limit: int
) -> CollectionsResponse:
    if language is None:
        language = get("DEFAULT_LANGUAGE") or "en"

    client = get_open_pecha_client()
    
    parent_id_param = parent_id if parent_id else UNSET
    
    categories: List[CategoryOutput] = await get_v2_categories.asyncio(
        client=client,
        parent_id=parent_id_param,
        language=language,
        x_application=X_APPLICATION
    )
    
    if categories is None:
        categories = []
    
    if not isinstance(categories, list):
        categories = []
    
    collection_list = [
        _category_to_collection_model(category, language)
        for category in categories
    ]
    
    total = len(collection_list)
    paginated_collections = collection_list[skip:skip + limit]
    
    parent_collection = None
    if parent_id:
        parent_categories = await get_v2_categories.asyncio(
            client=client,
            parent_id=UNSET,
            language=language,
            x_application=X_APPLICATION
        )
        if parent_categories and isinstance(parent_categories, list):
            for cat in parent_categories:
                if cat.id == parent_id:
                    parent_collection = _category_to_collection_model(cat, language)
                    break
    
    pagination = Pagination(total=total, skip=skip, limit=limit)
    
    return CollectionsResponse(
        parent=parent_collection,
        pagination=pagination,
        collections=paginated_collections
    )
