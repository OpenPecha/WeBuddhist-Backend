from pecha_api.recitations.recitations_enum import LanguageCode,RecitationListTextType
from pecha_api.texts.texts_enums import TextType
from typing import List, Dict, Union,Optional
from pecha_api.collections.collections_repository import get_all_collections_by_parent, get_collection_id_by_slug
from pecha_api.collections.collections_service import get_collection
from pecha_api.recitations.recitations_repository import apply_search_recitation_title_filter
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
from pecha_api.texts.segments.segments_service import get_segment_by_id, get_related_mapped_segments, get_segment_details_by_id
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


async def get_list_of_recitations_service(search: Optional[str] = None, language: str = "en") -> RecitationsResponse:
    collection_id = await get_collection_id_by_slug(slug="Liturgy")
    if collection_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.COLLECTION_NOT_FOUND)
    
    recitation_list_text_response: RecitationsResponse = await get_root_text_by_collection_id(collection_id=collection_id, language=language)

    serched_texts=apply_search_recitation_title_filter(texts=recitation_list_text_response.recitations, search=search)
    return RecitationsResponse(recitations=serched_texts)


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


async def segments_mapping_by_toc(table_of_contents: List[TableOfContent], recitation_details_request: RecitationDetailsRequest) -> List[Segment]:
    filter_mapped_segments = []
    for table_of_content in table_of_contents:
        section = table_of_content.sections[0]

        for segment in section.segments:
            recitation_segment = RecitationSegment()
            mapped_segments = []
            segment_details = await get_segment_details_by_id(segment_id=segment.segment_id, text_details=True)
            segment_model = SegmentDTO(
                id=segment_details.id,
                text_id=segment_details.text_id,
                content=segment_details.content,
                mapping=segment_details.mapping,
                type=segment_details.type
            )
            
            mapped_segments = await get_related_mapped_segments(parent_segment_id=segment.segment_id)
            mapped_segments.append(segment_model)
            
            recitations = await SegmentUtils.filter_segment_mapping_by_type_or_text_id(segments=mapped_segments, type= TextType.VERSION.value)
            translations = await SegmentUtils.filter_segment_mapping_by_type_or_text_id(segments=mapped_segments, type= TextType.VERSION.value)
            transliterations = await SegmentUtils.filter_segment_mapping_by_type_or_text_id(segments=mapped_segments, type=TextType.VERSION.value)
            adaptations = await SegmentUtils.filter_segment_mapping_by_type_or_text_id(segments=mapped_segments, type=TextType.VERSION.value)


            for type, segments, langs in [
                (RecitationListTextType.RECITATIONS.value, recitations, recitation_details_request.recitation),
                (RecitationListTextType.TRANSLATIONS.value, translations, recitation_details_request.translations),
                (RecitationListTextType.TRANSLITERATIONS.value, transliterations, recitation_details_request.transliterations),
                (RecitationListTextType.ADAPTATIONS.value, adaptations, recitation_details_request.adaptations),
            ]:
                if type == RecitationListTextType.RECITATIONS.value:
                    recitation_segment.recitation = filter_by_type_and_language(type=type, segments=segments, languages=langs)
                elif type == RecitationListTextType.TRANSLATIONS.value:
                    recitation_segment.translations = filter_by_type_and_language(type=type, segments=segments, languages=langs)
                elif type == RecitationListTextType.TRANSLITERATIONS.value:
                    recitation_segment.transliterations = filter_by_type_and_language(type=type, segments=segments, languages=langs)
                elif type == RecitationListTextType.ADAPTATIONS.value:
                    recitation_segment.adaptations = filter_by_type_and_language(type=type, segments=segments, languages=langs)
           
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