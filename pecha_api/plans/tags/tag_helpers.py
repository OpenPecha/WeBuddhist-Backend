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
    language: str = 'EN',
) -> List[TagSummaryDTO]:
    if not tags:
        return []
    active = [t for t in tags if t.deleted_at is None]
    dtos = []
    
    for tag in active:
        # Get name and description from metadata for the specified language
        name = ""
        description = None
        
        if hasattr(tag, 'metadata_entries') and tag.metadata_entries:
            for meta in tag.metadata_entries:
                lang_value = meta.language.value if hasattr(meta.language, 'value') else str(meta.language)
                if lang_value == language:
                    name = meta.name
                    description = meta.description
                    break
            
            # Fallback to first metadata entry if requested language not found
            if not name and tag.metadata_entries:
                first_meta = tag.metadata_entries[0]
                name = first_meta.name
                description = first_meta.description
        
        dtos.append(TagSummaryDTO(
            id=tag.id,
            name=name,
            image=generate_tag_image_url(tag.image_key),
            image_key=tag.image_key,
            description=description,
            featured=tag.featured,
            display_order=tag.display_order,
        ))
    
    if preserve_order:
        return dtos
    return sorted(
        dtos,
        key=lambda item: (
            item.display_order is None,
            item.display_order if item.display_order is not None else 0,
            item.name.lower() if item.name else "",
        ),
    )
