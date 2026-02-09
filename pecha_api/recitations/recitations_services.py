from pecha_api.recitations.recitations_enum import LanguageCode,RecitationListTextType
from pecha_api.texts.texts_enums import TextType
from typing import List, Dict, Union,Optional
from pecha_api.collections.collections_repository import get_all_collections_by_parent, get_collection_id_by_slug
from pecha_api.collections.collections_service import get_collection
from pecha_api.recitations.recitations_repository import apply_search_recitation_title_filter, get_text_images_by_text_ids
from pecha_api.recitations.recitations_response_models import RecitationDTO, RecitationsResponse
from pecha_api.texts.texts_repository import get_all_texts_by_collection
from pecha_api.texts.texts_service import get_root_text_by_collection_id
from fastapi import HTTPException
from starlette import status
from uuid import UUID

from pecha_api.error_contants import ErrorConstants
from pecha_api.texts.texts_utils import TextUtils
from pecha_api.texts.texts_response_models import TextDTO, TableOfContent
from pecha_api.texts.texts_repository import get_contents_by_id, get_all_texts_by_group_id
from pecha_api.texts.segments.segments_service import get_segment_by_id, get_related_mapped_segments, get_segment_details_by_id, get_related_mapped_segments_batch, get_segments_details_by_ids
from pecha_api.texts.segments.segments_utils import SegmentUtils
from pecha_api.texts.segments.segments_response_models import SegmentTranslation, SegmentTransliteration, SegmentAdaptation, SegmentRecitation
from pecha_api.texts.segments.segments_response_models import SegmentDTO
from pecha_api.recitations.recitations_response_models import (
    RecitationDTO, 
    RecitationsResponse, 
    RecitationDetailsRequest, 
    RecitationDetailsResponse,
    Segment,
    RecitationSegment,  
    RecitationsResponse
)
from pecha_api.cache.cache_enums import CacheType
from pecha_api.recitations.recication_cache_services import set_recitation_by_text_id_cache, get_recitation_by_text_id_cache
from pecha_api.db.database import SessionLocal
from pecha_api.uploads.S3_utils import generate_presigned_access_url
from pecha_api.config import get

def get_recitations_with_image_urls(recitations: List[RecitationDTO]) -> List[RecitationDTO]:
    text_ids = [str(recitation.text_id) for recitation in recitations]
    
    with SessionLocal() as db_session:
        image_keys = get_text_images_by_text_ids(db=db_session, text_ids=text_ids)

    image_url_map: Dict[str, str] = {
        text_id: generate_presigned_access_url(
            bucket_name=get("AWS_BUCKET_NAME"), s3_key=s3_key
        )
        for text_id, s3_key in image_keys.items()
    }

    recitations_with_images = [
        RecitationDTO(
            title=recitation.title,
            text_id=recitation.text_id,
            image_url=image_url_map.get(str(recitation.text_id)),
        )
        for recitation in recitations
    ]

    return recitations_with_images

async def get_list_of_recitations_service(search: Optional[str] = None, language: str = "en") -> RecitationsResponse:
    collection_id = await get_collection_id_by_slug(slug="Liturgy")
    if collection_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.COLLECTION_NOT_FOUND)
    
    recitation_list_text_response: RecitationsResponse = await get_root_text_by_collection_id(collection_id=collection_id, language=language)

    serched_texts=apply_search_recitation_title_filter(texts=recitation_list_text_response.recitations, search=search)
    recitations_with_images = get_recitations_with_image_urls(recitations=serched_texts)
    
    return RecitationsResponse(recitations=recitations_with_images)


async def get_recitation_details_service(text_id: str, recitation_details_request: RecitationDetailsRequest) -> RecitationDetailsResponse:
    is_valid_text: bool = await TextUtils.validate_text_exists(text_id=text_id)
    if not is_valid_text:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE)
        
    cached_data: RecitationDetailsResponse = await get_recitation_by_text_id_cache(text_id=text_id, recitation_details_request=recitation_details_request, cache_type=CacheType.RECITATION_DETAILS)
    if cached_data is not None:
        return cached_data

    text_detail: TextDTO = await get_text_details_by_text_id(text_id=text_id)

    group_id: str = text_detail.group_id
    texts: List[TextDTO] = await get_all_texts_by_group_id(group_id=group_id)
    
    filtered_text_on_root_and_version = TextUtils.filter_text_on_root_and_version(texts=texts, language=recitation_details_request.language)
    root_text: TextDTO = filtered_text_on_root_and_version[TextType.ROOT_TEXT.value]
    if root_text is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE)
    table_of_contents: List[TableOfContent] = await get_contents_by_id(text_id=root_text.id)
    segments = await segments_mapping_by_toc(table_of_contents=table_of_contents, recitation_details_request=recitation_details_request)

    recitation_details_response = RecitationDetailsResponse(
        text_id=UUID(text_detail.id),
        title=text_detail.title,
        segments=segments   
    )

    await set_recitation_by_text_id_cache(
        text_id=text_id, 
        recitation_details_request=recitation_details_request, 
        cache_type=CacheType.RECITATION_DETAILS, 
        data=recitation_details_response
    )

   
    return recitation_details_response

async def get_text_details_by_text_id(text_id: str) -> TextDTO:
    return await TextUtils.get_text_detail_by_id(text_id=text_id)


async def _filter_and_map_segments(
    all_segments: List[SegmentDTO],
    filter_type: str,
    languages: List[str]
) -> Dict[str, Segment]:
    """Helper to filter segments by type and language."""
    filtered = await SegmentUtils.filter_segment_mapping_by_type_or_text_id(
        segments=all_segments,
        type=TextType.VERSION.value
    )
    return filter_by_type_and_language(
        type=filter_type,
        segments=filtered,
        languages=languages
    )


async def segments_mapping_by_toc(table_of_contents: List[TableOfContent], recitation_details_request: RecitationDetailsRequest) -> List[Segment]:

    needs_recitation = bool(recitation_details_request.recitation)
    needs_translations = bool(recitation_details_request.translations)
    needs_transliterations = bool(recitation_details_request.transliterations)
    needs_adaptations = bool(recitation_details_request.adaptations)
    
    needs_mapped_segments = needs_translations or needs_transliterations or needs_adaptations
    
    all_segment_ids = []
    for table_of_content in table_of_contents:
        section = table_of_content.sections[0]
        for segment in section.segments:
            all_segment_ids.append(segment.segment_id)
    
    if not all_segment_ids:
        return []
    
    segment_details_dict = await get_segments_details_by_ids(segment_ids=all_segment_ids)
    
    mapped_segments_dict = {}
    if needs_mapped_segments:
        mapped_segments_dict = await get_related_mapped_segments_batch(parent_segment_ids=all_segment_ids)
    
    filter_mapped_segments = []
    for table_of_content in table_of_contents:
        section = table_of_content.sections[0]

        for segment in section.segments:
            recitation_segment = RecitationSegment()
            segment_id = segment.segment_id
            
            segment_details = segment_details_dict.get(segment_id)
            if not segment_details:
                continue
                
            segment_model = SegmentDTO(
                id=segment_details.id,
                text_id=segment_details.text_id,
                content=segment_details.content,
                mapping=segment_details.mapping,
                type=segment_details.type
            )
            
            all_segments_for_filter = [segment_model]
            
            if needs_mapped_segments:
                mapped_for_segment = mapped_segments_dict.get(segment_id, [])
                all_segments_for_filter.extend(mapped_for_segment)
            
            if needs_recitation:
                recitation_segment.recitation = await _filter_and_map_segments(
                    all_segments=all_segments_for_filter,
                    filter_type=RecitationListTextType.RECITATIONS.value,
                    languages=recitation_details_request.recitation
                )
            
            if needs_translations:
                recitation_segment.translations = await _filter_and_map_segments(
                    all_segments=all_segments_for_filter,
                    filter_type=RecitationListTextType.TRANSLATIONS.value,
                    languages=recitation_details_request.translations
                )
            
            if needs_transliterations:
                recitation_segment.transliterations = await _filter_and_map_segments(
                    all_segments=all_segments_for_filter,
                    filter_type=RecitationListTextType.TRANSLITERATIONS.value,
                    languages=recitation_details_request.transliterations
                )
            
            if needs_adaptations:
                recitation_segment.adaptations = await _filter_and_map_segments(
                    all_segments=all_segments_for_filter,
                    filter_type=RecitationListTextType.ADAPTATIONS.value,
                    languages=recitation_details_request.adaptations
                )
           
            filter_mapped_segments.append(recitation_segment)
    return filter_mapped_segments

def filter_by_type_and_language(type:str,segments: List[Union[SegmentRecitation, SegmentTranslation, SegmentTransliteration, SegmentAdaptation]],languages: List[str]) -> Dict[str, Segment]:
    filtered_segments = {
        segment.language: Segment(
            id=segment.segment_id,
            content=segment.content 
        )
        for segment in segments
        if segment.language in languages
    }
    return filtered_segments
