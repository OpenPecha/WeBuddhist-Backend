import logging
from typing import Optional

from beanie.exceptions import CollectionWasNotInitialized

from pecha_api.utils import Utils
from ..collections.collections_models import Collection


async def get_all_collections_by_parent(
        parent_id: Optional[str]) -> list[Collection]:
    try:
        topic_parent_id = Utils.get_parent_id(parent_id=parent_id)
        collections = await Collection.get_all_children_by_id(parent_id=topic_parent_id)
        return collections
    except CollectionWasNotInitialized as e:
        logging.debug(e)
        return []

async def get_collection_by_id(collection_id: Optional[str]) -> Optional[Collection]:
    if not collection_id:
        return None
    return await Collection.get(collection_id)


async def get_collection_id_by_slug(slug: str) -> Optional[str]:
    collection = await Collection.get_by_slug(slug=slug)
    if collection:
        return str(collection.id)
    return None


async def get_collection_id_by_pecha_collection_id(pecha_collection_id: str) -> Optional[str]:
    collection = await Collection.get_by_pecha_collection_id(pecha_collection_id=pecha_collection_id)
    if collection:
        return str(collection.id)
    return None