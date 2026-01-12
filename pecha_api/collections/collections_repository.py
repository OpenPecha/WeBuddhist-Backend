import logging
from typing import Optional

from beanie.exceptions import CollectionWasNotInitialized
from fastapi import HTTPException
from starlette import status

from pecha_api.utils import Utils
from ..collections.collections_models import Collection
from ..collections.collections_response_models import CreateCollectionRequest, UpdateCollectionRequest

COLLECTION_NOT_FOUND = 'Collection not found'


async def get_collections_by_parent(
        parent_id: Optional[str],
        skip: int,
        limit: int) -> list[Collection]:
    try:
        topic_parent_id = Utils.get_parent_id(parent_id=parent_id)
        collections = await Collection.get_children_by_id(parent_id=topic_parent_id, skip=skip, limit=limit)
        return collections
    except CollectionWasNotInitialized as e:
        logging.debug(e)
        return []

async def get_all_collections_by_parent(
        parent_id: Optional[str]) -> list[Collection]:
    try:
        topic_parent_id = Utils.get_parent_id(parent_id=parent_id)
        collections = await Collection.get_all_children_by_id(parent_id=topic_parent_id)
        return collections
    except CollectionWasNotInitialized as e:
        logging.debug(e)
        return []

async def get_child_count(parent_id: Optional[str]) -> int:
    topic_parent_id = Utils.get_parent_id(parent_id=parent_id)
    count = await Collection.count_children(parent_id=topic_parent_id)
    return count


async def create_collection(create_collection_request: CreateCollectionRequest) -> Collection:
    try:
        existing_collection = await Collection.find_one(Collection.slug == create_collection_request.slug)
        if existing_collection:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Collection with this slug {create_collection_request.slug} already exists")
    except AttributeError as e:
        logging.debug(e)
    new_collection = Collection(pecha_collection_id=create_collection_request.pecha_collection_id, slug=create_collection_request.slug, titles=create_collection_request.titles,
                    descriptions=create_collection_request.descriptions, parent_id=create_collection_request.parent_id)
    saved_collection = await new_collection.insert()
    if create_collection_request.parent_id is not None:
        await update_collection_child_status(collection_id=create_collection_request.parent_id)
    return saved_collection


async def get_collection_by_id(collection_id: Optional[str]) -> Optional[Collection]:
    if not collection_id:
        return None
    return await Collection.get(collection_id)


async def update_collection_child_status(collection_id: str) -> Collection:
    existing_collection = await Collection.get(collection_id)
    if not existing_collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=COLLECTION_NOT_FOUND)
    child_count = await Collection.count_children(parent_id=existing_collection.id)
    has_child = child_count > 0
    if existing_collection.has_sub_child != has_child:
        existing_collection.has_sub_child = has_child
        await existing_collection.save()
    return existing_collection


async def update_collection_titles(collection_id: str, update_collection_request: UpdateCollectionRequest) -> Collection:
    existing_collection = await Collection.get(collection_id)
    if not existing_collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=COLLECTION_NOT_FOUND)

    existing_collection.titles = update_collection_request.titles
    await existing_collection.save()
    return existing_collection


async def delete_collection(collection_id: str):
    existing_collection = await Collection.get(collection_id)
    if not existing_collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=COLLECTION_NOT_FOUND)
    parent_id = existing_collection.parent_id
    await existing_collection.delete()
    if parent_id is not None:
        await update_collection_child_status(collection_id=str(parent_id))
    return existing_collection

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