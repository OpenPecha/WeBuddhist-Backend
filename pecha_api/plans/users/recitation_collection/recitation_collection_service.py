import logging
from uuid import UUID
from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.config import get
from pecha_api.users.users_service import validate_and_extract_user_details
from pecha_api.texts.texts_repository import get_texts_by_ids
from pecha_api.uploads.S3_utils import generate_presigned_access_url
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import NOT_FOUND

from pecha_api.plans.users.recitation_collection.recitation_collection_repository import (
    get_user_collections,
    get_collection_item_counts,
    get_collection_by_id,
    get_collection_items
)
from pecha_api.plans.users.recitation_collection.recitation_collection_response_models import (
    RecitationCollectionDTO,
    RecitationCollectionDetailDTO,
    RecitationCollectionItemDTO,
    RecitationCollectionsResponse
)

logger = logging.getLogger(__name__)


def _generate_presigned_url(s3_key: str) -> str | None:
    """Safely generate presigned URL for S3 key."""
    if not s3_key:
        return None
    try:
        return generate_presigned_access_url(
            bucket_name=get("AWS_BUCKET_NAME"),
            s3_key=s3_key
        )
    except Exception as e:
        logger.error(f"Failed to generate presigned URL for {s3_key}: {e}")
        return None


async def get_user_collections_service(
    token: str,
    skip: int = 0,
    limit: int = 20
) -> RecitationCollectionsResponse:

    current_user = validate_and_extract_user_details(token=token)
    
    with SessionLocal() as db:
        collections, total = get_user_collections(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
        
        if not collections:
            return RecitationCollectionsResponse(
                collections=[],
                skip=skip,
                limit=limit,
                total=0
            )
        
        collection_ids = [c.id for c in collections]
        item_counts = get_collection_item_counts(db=db, collection_ids=collection_ids)
        
        collections_dto = [
            RecitationCollectionDTO(
                id=collection.id,
                name=collection.name,
                img_url=_generate_presigned_url(collection.img_url),
                item_count=item_counts.get(collection.id, 0),
                created_at=collection.created_at,
                updated_at=collection.updated_at
            )
            for collection in collections
        ]
        
        return RecitationCollectionsResponse(
            collections=collections_dto,
            skip=skip,
            limit=limit,
            total=total
        )


async def get_collection_detail_service(
    token: str,
    collection_id: UUID
) -> RecitationCollectionDetailDTO:

    current_user = validate_and_extract_user_details(token=token)
    
    with SessionLocal() as db:
        collection = get_collection_by_id(
            db=db,
            collection_id=collection_id,
            user_id=current_user.id
        )
        
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ResponseError(error=NOT_FOUND, message=f"Collection with ID {collection_id} not found").model_dump()
            )
        
        items = get_collection_items(db=db, collection_id=collection_id)
        
        if not items:
            return RecitationCollectionDetailDTO(
                id=collection.id,
                name=collection.name,
                img_url=_generate_presigned_url(collection.img_url),
                created_at=collection.created_at,
                updated_at=collection.updated_at,
                items=[]
            )
        
        text_ids = [str(item.text_id) for item in items]
        texts_dict = await get_texts_by_ids(text_ids=text_ids)
        
        items_dto = []
        for item in items:
            text_id_str = str(item.text_id)
            if text_id_str in texts_dict:
                text = texts_dict[text_id_str]
                items_dto.append(
                    RecitationCollectionItemDTO(
                        id=item.id,
                        text_id=item.text_id,
                        title=text.title,
                        language=text.language,
                        type=text.type,
                        display_order=item.display_order
                    )
                )
        
        return RecitationCollectionDetailDTO(
            id=collection.id,
            name=collection.name,
            img_url=_generate_presigned_url(collection.img_url),
            created_at=collection.created_at,
            updated_at=collection.updated_at,
            items=items_dto
        )
