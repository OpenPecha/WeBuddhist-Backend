from uuid import UUID
from typing import Dict, List

from pecha_api.db.database import SessionLocal
from pecha_api.texts.texts_utils import TextUtils
from pecha_api.texts.texts_repository import get_texts_by_ids
from pecha_api.users.users_service import validate_and_extract_user_details
from pecha_api.plans.users.recitation.user_recitations_models import UserRecitations
from pecha_api.plans.users.recitation.user_recitations_repository import (
    save_user_recitation,
    get_user_recitations_by_user_id,
    get_max_display_order_for_user,
    update_recitation_order_in_bulk,
    delete_user_recitation,
)
from pecha_api.plans.users.recitation.user_recitations_response_models import (
    CreateUserRecitationRequest,
    UserRecitationsResponse,
    UserRecitationDTO,
    UserRecitationItemType,
    UpdateRecitationOrderRequest,
)
from pecha_api.plans.users.recitation_collection.recitation_collection_repository import (
    get_all_user_collections,
    get_collection_item_counts,
)
from pecha_api.plans.groups.groups_repository import get_following_group_ids_by_user
from pecha_api.group_recitation_collection.repository import (
    get_collections_by_group_ids,
    get_collection_item_counts as get_group_collection_item_counts,
)
from pecha_api.recitations.recitations_repository import get_text_images_by_text_ids
from pecha_api.uploads.S3_utils import generate_presigned_access_url
from pecha_api.config import get


def get_image_url_map_by_text_ids(db, text_ids: list) -> Dict[str, str]:
    image_keys = get_text_images_by_text_ids(db=db, text_ids=text_ids)

    image_url_map = {
        text_id: generate_presigned_access_url(
            bucket_name=get("AWS_BUCKET_NAME"),
            s3_key=s3_key,
        )
        for text_id, s3_key in image_keys.items()
    }

    return image_url_map


def _presigned_image_url(s3_key: str | None) -> str | None:
    if not s3_key:
        return None
    return generate_presigned_access_url(
        bucket_name=get("AWS_BUCKET_NAME"),
        s3_key=s3_key,
    )


def _build_individual_collection_dtos(db, user_id: UUID) -> List[UserRecitationDTO]:
    collections = get_all_user_collections(db=db, user_id=user_id)
    if not collections:
        return []

    item_counts = get_collection_item_counts(
        db=db,
        collection_ids=[collection.id for collection in collections],
    )
    return [
        UserRecitationDTO(
            type=UserRecitationItemType.RECITATION_COLLECTION,
            name=collection.name,
            collection_id=collection.id,
            image_url=_presigned_image_url(collection.img_url),
            item_count=item_counts.get(collection.id, 0),
        )
        for collection in collections
    ]


def _build_group_collection_dtos(db, user_id: UUID) -> List[UserRecitationDTO]:
    followed_group_ids = get_following_group_ids_by_user(db=db, user_id=user_id)
    collections = get_collections_by_group_ids(db=db, group_ids=followed_group_ids)
    if not collections:
        return []

    item_counts = get_group_collection_item_counts(
        db=db,
        collection_ids=[collection.id for collection in collections],
    )
    return [
        UserRecitationDTO(
            type=UserRecitationItemType.GROUP_RECITATION_COLLECTION,
            name=collection.name,
            collection_id=collection.id,
            group_id=collection.group_id,
            image_url=_presigned_image_url(collection.img_url),
            item_count=item_counts.get(collection.id, 0),
        )
        for collection in collections
    ]


async def _build_recitation_dtos(db, user_id: UUID) -> List[UserRecitationDTO]:
    user_recitations = get_user_recitations_by_user_id(db=db, user_id=user_id)
    if not user_recitations:
        return []

    text_ids = [str(recitation.text_id) for recitation in user_recitations]
    texts_dict = await get_texts_by_ids(text_ids=text_ids)
    image_url_map = get_image_url_map_by_text_ids(db=db, text_ids=text_ids)

    return [
        UserRecitationDTO(
            type=UserRecitationItemType.RECITATION,
            title=texts_dict[str(recitation.text_id)].title,
            text_id=recitation.text_id,
            image_url=image_url_map.get(str(recitation.text_id)),
            language=texts_dict[str(recitation.text_id)].language,
            display_order=recitation.display_order,
        )
        for recitation in user_recitations
        if str(recitation.text_id) in texts_dict
    ]


async def create_user_recitation_service(
    token: str, create_user_recitation_request: CreateUserRecitationRequest
) -> None:
    current_user = validate_and_extract_user_details(token=token)
    with SessionLocal() as db:
        await TextUtils.validate_text_exists(
            text_id=str(create_user_recitation_request.text_id)
        )

        max_order = get_max_display_order_for_user(db=db, user_id=current_user.id)
        next_order = (max_order or 0) + 1

        new_user_recitations = UserRecitations(
            user_id=current_user.id,
            text_id=create_user_recitation_request.text_id,
            display_order=next_order,
        )
        save_user_recitation(db=db, user_recitations=new_user_recitations)


async def get_user_recitations_service(
    token: str,
    include_collections: bool = False,
    include_group_collections: bool = False,
) -> UserRecitationsResponse:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        items: List[UserRecitationDTO] = []

        if include_collections:
            items.extend(
                _build_individual_collection_dtos(db=db, user_id=current_user.id)
            )

        if include_group_collections:
            items.extend(
                _build_group_collection_dtos(db=db, user_id=current_user.id)
            )

        items.extend(await _build_recitation_dtos(db=db, user_id=current_user.id))

        return UserRecitationsResponse(recitations=items)


async def update_recitation_order_service(
    token: str, update_order_request: UpdateRecitationOrderRequest
) -> None:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        recitation_updates = [
            {"text_id": item.text_id, "display_order": item.display_order}
            for item in update_order_request.recitations
        ]
        update_recitation_order_in_bulk(
            db=db, user_id=current_user.id, recitation_updates=recitation_updates
        )


async def delete_user_recitation_service(token: str, text_id: UUID) -> None:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        delete_user_recitation(db=db, user_id=current_user.id, text_id=text_id)
