from typing import List, Optional

from pecha_api.config import get
from pecha_api.plans.tags.tag_model import Tag
from pecha_api.plans.tags.tag_response_models import TagSummaryDTO
from pecha_api.uploads.S3_utils import generate_presigned_access_url


def generate_tag_image_url(image_key: Optional[str]) -> Optional[str]:
    if not image_key:
        return None
    return generate_presigned_access_url(
        bucket_name=get("AWS_BUCKET_NAME"),
        s3_key=image_key,
    )


def tags_to_summary_dtos(
    tags: Optional[List[Tag]],
    *,
    preserve_order: bool = False,
) -> List[TagSummaryDTO]:
    if not tags:
        return []
    active = [t for t in tags if t.deleted_at is None]
    dtos = [
        TagSummaryDTO(
            id=tag.id,
            name=tag.name,
            image=generate_tag_image_url(tag.image_key),
            image_key=tag.image_key,
            description=tag.description,
            featured=tag.featured,
        )
        for tag in active
    ]
    if preserve_order:
        return dtos
    return sorted(dtos, key=lambda item: item.name.lower())
