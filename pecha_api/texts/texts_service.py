from fastapi import HTTPException
from starlette import status

from pecha_api.error_contants import ErrorConstants
from .texts_repository import (
    get_all_texts_by_collection,
    get_texts_by_collection,
    get_texts_by_group_id,
    create_text,
    create_table_of_content_detail,
    get_contents_by_id,
    get_table_of_content_by_content_id,
    get_sections_count_of_table_of_content,
    delete_table_of_content_by_text_id,
    update_text_details_by_id,
    delete_text_by_id,
    fetch_sheets_from_db,
    get_all_texts_by_collection,
    get_all_recitation_texts_by_collection,
    get_texts_by_pecha_text_ids
)
from .texts_response_models import (
    TableOfContent,
    TableOfContentType,
    DetailTableOfContentResponse,
    TableOfContentResponse,
    TextDTO,
    TextSegment,
    TextVersionResponse,
    TextVersion,
    TextsCategoryResponse,
    CreateTextRequest,
    TextDetailsRequest,
    UpdateTextRequest,
    TextDetailsRequest,
    Section,
    DetailTableOfContentResponse,
    TextsByPechaTextIdsRequest
)

from pecha_api.recitations.recitations_response_models import(
     RecitationDTO, 
     RecitationsResponse
)

from pecha_api.constants import Constants

from .groups.groups_service import (
    validate_group_exists
)
from .segments.segments_models import Segment
from pecha_api.texts.texts_cache_service import (
    set_text_details_cache,
    get_text_details_cache,
    get_text_by_text_id_or_collection_cache,
    set_text_by_text_id_or_collection_cache,
    get_table_of_contents_by_text_id_cache,
    set_table_of_contents_by_text_id_cache,
    get_text_versions_by_group_id_cache,
    set_text_versions_by_group_id_cache,
    get_table_of_content_by_sheet_id_cache,
    set_table_of_content_by_sheet_id_cache,
    delete_table_of_content_by_sheet_id_cache,
    update_text_details_cache,
    invalidate_text_cache_on_update
)
from .segments.segments_repository import get_segments_by_text_id
from pecha_api.sheets.sheets_enum import (
    SortBy,
    SortOrder
)
from pecha_api.cache.cache_enums import CacheType

from .texts_utils import TextUtils
from pecha_api.users.users_service import validate_user_exists
from pecha_api.collections.collections_service import get_collection
from pecha_api.users.users_service import (
    validate_user_exists
)
from .segments.segments_utils import SegmentUtils

from typing import List, Dict, Optional, Tuple, Set
from pecha_api.config import get
from pecha_api.utils import Utils
from .texts_enums import PaginationDirection, LANGUAGE_ORDERS, TextType, TextTypes

import logging


async def get_text_by_text_id_or_collection(
        text_id: str,
        collection_id: Optional[str] = None,
        language: Optional[str] = None,
        skip: int = 0,
        limit: int = 10
) -> TextsCategoryResponse | TextDTO:
    if language is None:
        language = get("DEFAULT_LANGUAGE")

    cached_data: TextsCategoryResponse | TextDTO = await get_text_by_text_id_or_collection_cache(
        text_id = text_id,
        collection_id = collection_id,
        language = language,
        skip = skip,
        limit = limit,
        cache_type = CacheType.TEXTS_BY_ID_OR_COLLECTION
    )

    if cached_data is not None:
        return cached_data

    if collection_id is not None:
        collection = await get_collection(collection_id=collection_id, language=language)
        texts, total_unique_group_ids = await _get_texts_by_collection_id(collection_id=collection_id, language=language, skip=skip, limit=limit)
    
        response = TextsCategoryResponse(
            collection=collection,
            texts=texts,
            total=total_unique_group_ids,
            skip=skip,
            limit=limit
        )
    else:
        response = await TextUtils.get_text_detail_by_id(text_id=text_id)
    
    await set_text_by_text_id_or_collection_cache(
        text_id = text_id,
        collection_id = collection_id,
        language = language,
        skip = skip,
        limit = limit,
        cache_type = CacheType.TEXTS_BY_ID_OR_COLLECTION,
        data = response
    )
    return response


async def get_sheet(published_by: Optional[str] = None, is_published: Optional[bool] = None, sort_by: Optional[SortBy] = None, sort_order: Optional[SortOrder] = None, skip: int = 0, limit: int = 10):
    
    sheets = await fetch_sheets_from_db(
        published_by=published_by,
        is_published=is_published,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit
    )
    return sheets

async def get_table_of_content_by_sheet_id(sheet_id: str) -> Optional[TableOfContent]:
    cached_data: TableOfContent = await get_table_of_content_by_sheet_id_cache(sheet_id=sheet_id, cache_type=CacheType.SHEET_TABLE_OF_CONTENT)
    if cached_data is not None:
        return cached_data
    
    table_of_content = None
    is_valid_sheet: bool = await TextUtils.validate_text_exists(text_id=sheet_id)
    if not is_valid_sheet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE)
    
    table_of_contents: List[TableOfContent] = await get_contents_by_id(text_id=sheet_id)
    if len(table_of_contents) > 0 and table_of_contents[0] is not None:
        table_of_content: TableOfContent = table_of_contents[0]
    
    if table_of_content is not None:
        await set_table_of_content_by_sheet_id_cache(sheet_id=sheet_id, cache_type=CacheType.SHEET_TABLE_OF_CONTENT, data=table_of_content)
    
    return table_of_content

async def get_table_of_contents_by_text_id(text_id: str, language: str = None, skip: int = 0, limit: int = 10) -> TableOfContentResponse:
    
    if language is None:
        language = get("DEFAULT_LANGUAGE")
    
    is_valid_text: bool = await TextUtils.validate_text_exists(text_id=text_id)
    if not is_valid_text:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE)
    
    text_detail: TextDTO = await TextUtils.get_text_detail_by_id(text_id=text_id)
    group_id: str = text_detail.group_id
    texts: List[TextDTO] = await get_texts_by_group_id(group_id=group_id, skip=skip, limit=limit)
    filtered_text_on_root_and_version = TextUtils.filter_text_on_root_and_version(texts=texts, language=language)
    root_text: TextDTO = filtered_text_on_root_and_version[TextType.ROOT_TEXT.value]
    if root_text is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE)
    table_of_contents: List[TableOfContent] = await get_contents_by_id(text_id=root_text.id)

    response = TableOfContentResponse(
        text_detail=root_text,
        contents=[
            TableOfContent(
                id=str(content.id),
                text_id=content.text_id,
                type=content.type if content.type else TableOfContentType.TEXT,
                sections=_get_paginated_sections(sections=content.sections, skip=skip, limit=limit)
            )
            for content in table_of_contents
        ]
    )
    
    return response

def _get_paginated_sections(sections: List[Section], skip: int, limit: int) -> List[Section]:
    filtered_sections = [] 
    skip_index = skip
    limit_index = skip + limit
    for section in sections:
        first_segment = section.segments[0]
        if section.segments:
            new_section = Section(
                id=section.id,
                title=section.title,
                section_number=section.section_number,
                parent_id=section.parent_id,
                segments=[first_segment],
                sections=section.sections if section.sections else None,
                created_date=section.created_date,
                updated_date=section.updated_date,
                published_date=section.published_date
            )
            filtered_sections.append(new_section)

    return filtered_sections[skip_index:limit_index]

async def remove_table_of_content_by_text_id(text_id: str):
    is_valid_text = await TextUtils.validate_text_exists(text_id=text_id)
    if not is_valid_text:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE)
    return await delete_table_of_content_by_text_id(text_id=text_id)


# NEW TEXT DETAILS SERVICE
async def get_text_details_by_text_id(
        text_id: str,
        text_details_request: TextDetailsRequest
) -> DetailTableOfContentResponse:
    
    await _validate_text_detail_request(
        text_id=text_id,
        text_details_request=text_details_request
    )
    selected_text = await TextUtils.get_text_detail_by_id(text_id=text_id)
    
    table_of_content: TableOfContent = await _receive_table_of_content(
        text_id=text_id,
        text_details_request=text_details_request
    )
    segments_with_position: List[Tuple[str, int]] = _get_segments_with_position_(
        table_of_content=table_of_content,
    )
    total_segments = len(segments_with_position)
    trimmed_segment_dict = _get_trimmed_segment_dict_(
        segments_with_position=segments_with_position,
        segment_id=text_details_request.segment_id,
        direction=text_details_request.direction,
        size=text_details_request.size
    )
    current_segment_position = trimmed_segment_dict.get(text_details_request.segment_id)
    paginated_table_of_content: TableOfContent = _generate_paginated_table_of_content_by_segments_(
        table_of_content = table_of_content,
        segment_dict = trimmed_segment_dict
    )

    detail_table_of_content: DetailTableOfContentResponse = await _mapping_table_of_content(
        text=selected_text,
        table_of_content=paginated_table_of_content,
        version_id=text_details_request.version_id,
        size=text_details_request.size,
        total_segments=total_segments,
        current_segment_position=current_segment_position,
        pagination_direction=text_details_request.direction
    )

    return detail_table_of_content


async def get_text_versions_by_group_id(text_id: str, language: str, skip: int, limit: int) -> TextVersionResponse:
    '''
    This function will first retrive the group_id from the text_id details
    It will retrieve all the texts with same group_id
    Then root text will be determined by the language provied
    Left texts will be considered as versions
    '''
    if language is None:
        language = get("DEFAULT_LANGUAGE")
    
    # cached_data: TextVersionResponse = await get_text_versions_by_group_id_cache(
    #     text_id = text_id,
    #     language = language,
    #     skip = skip,
    #     limit = limit,
    #     cache_type = CacheType.TEXT_VERSIONS
    # )
    # if cached_data is not None:
    #     return cached_data
    
    root_text = await TextUtils.get_text_detail_by_id(text_id=text_id)
    group_id = root_text.group_id
    texts = await get_texts_by_group_id(group_id=group_id, skip=skip, limit=limit)
    filtered_text_on_root_and_version = TextUtils.filter_text_on_root_and_version(texts=texts, language=language)
    root_text = filtered_text_on_root_and_version[TextType.ROOT_TEXT.value]
    versions = filtered_text_on_root_and_version[TextTypes.VERSIONS.value]
    versions_table_of_content_id_dict: Dict[str, List[str]] = await _get_table_of_content_by_version_text_id(versions=versions)
    list_of_version = _get_list_of_text_version_response_model(versions=versions, versions_table_of_content_id_dict=versions_table_of_content_id_dict)
    response = TextVersionResponse(
        text=root_text,
        versions=list_of_version
    )

    await set_text_versions_by_group_id_cache(
        text_id = text_id,
        language = language,
        skip = skip,
        limit = limit,
        cache_type = CacheType.TEXT_VERSIONS,
        data = response
    )

    return response


async def create_new_text(
        create_text_request: CreateTextRequest,
        token: str
) -> TextDTO:
    is_valid_user = validate_user_exists(token=token)
    if is_valid_user:
        valid_group = await validate_group_exists(group_id=create_text_request.group_id)
        if not valid_group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.GROUP_NOT_FOUND_MESSAGE)
        new_text = await create_text(create_text_request=create_text_request)
        return TextDTO(
            id=str(new_text.id),
            pecha_text_id=str(new_text.pecha_text_id),
            title=new_text.title,
            language=new_text.language,
            group_id=new_text.group_id,
            type=new_text.type,
            is_published=new_text.is_published,
            created_date=new_text.created_date,
            updated_date=new_text.updated_date,
            published_date=new_text.published_date,
            published_by=new_text.published_by,
            categories=new_text.categories,
            views=new_text.views,
            source_link=new_text.source_link,
            ranking=new_text.ranking,
            license=new_text.license
        )
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ErrorConstants.TOKEN_ERROR_MESSAGE)


async def create_table_of_content(table_of_content_request: TableOfContent, token: str):
    is_valid_user = validate_user_exists(token=token)
    
    if is_valid_user:
        await TextUtils.validate_text_exists(text_id=table_of_content_request.text_id)
        new_table_of_content = await get_table_of_content_by_type(table_of_content=table_of_content_request)
        segment_ids = TextUtils.get_all_segment_ids(table_of_content=new_table_of_content)
        await SegmentUtils.validate_segments_exists(segment_ids=segment_ids)
        table_of_content = await create_table_of_content_detail(table_of_content_request=new_table_of_content)
        return table_of_content
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ErrorConstants.TOKEN_ERROR_MESSAGE)
    



# PRIVATE FUNCTIONS

async def get_table_of_content_by_type(table_of_content: TableOfContent):
    if table_of_content.type == TableOfContentType.TEXT:
        new_table_of_content = await replace_pecha_segment_id_with_segment_id(table_of_content=table_of_content)
    else: 
        new_table_of_content = table_of_content
    
    return new_table_of_content
    


async def replace_pecha_segment_id_with_segment_id(table_of_content: TableOfContent) -> TableOfContent:
    text_segments = await get_segments_by_text_id(text_id=table_of_content.text_id)
    segments_dict = {segment.pecha_segment_id: segment.id for segment in text_segments}

    new_toc = TableOfContent(
        text_id=table_of_content.text_id,
        type=table_of_content.type,
        sections=[]
    )
    new_sections = []
    for section in table_of_content.sections:
        new_segments = []
        for segment in section.segments:
            # db_segment = await Segment.get_segment_by_pecha_segment_id(pecha_segment_id=segment.pecha_segment_id)
            new_segments.append(
                TextSegment(
                    segment_id=str(segments_dict[segment.segment_id]),
                    segment_number=segment.segment_number
                )
            )
        new_section = Section(
            id=section.id,
            title=section.title,
            section_number=section.section_number,
            segments=new_segments
        )
        new_sections.append(new_section)
    new_toc.sections = new_sections
    return new_toc

async def _mapping_table_of_content(
        text: TextDTO, 
        table_of_content: TableOfContent,
        version_id: str,
        size: int,
        total_segments: int,
        current_segment_position: int,
        pagination_direction: PaginationDirection,
) -> DetailTableOfContentResponse:
    detail_table_of_content = await SegmentUtils.get_mapped_segment_content_for_table_of_content(
        table_of_content=table_of_content,
        version_id=version_id
    )
    detail_table_of_content = DetailTableOfContentResponse(
        text_detail=text,
        content=detail_table_of_content,
        size=size,
        pagination_direction=pagination_direction,
        current_segment_position=current_segment_position,
        total_segments=total_segments
    )
    return detail_table_of_content


async def _validate_text_detail_request(text_id: str, text_details_request: TextDetailsRequest) -> bool:
    # Check if text_id is provided
    if text_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorConstants.TEXT_OR_TERM_NOT_FOUND_MESSAGE
        )

    # Check if valid version_id is provided
    if text_details_request.version_id is not None:
        await TextUtils.validate_text_exists(
            text_id=text_details_request.version_id
        )

    # Check if valid segment_id is provided
    if text_details_request.segment_id is not None:
        await SegmentUtils.validate_segment_exists(
            segment_id=text_details_request.segment_id
        )

    await TextUtils.validate_text_exists(text_id=text_id)

async def get_root_text_by_collection_id(collection_id: str, language: str) -> Optional[tuple[str, str]]:

    texts = await get_all_recitation_texts_by_collection(collection_id=collection_id, language=language)
    grouped_texts = _group_texts_by_group_id(texts=texts, language=language)
    recitation_text_list = []
    for group_texts in grouped_texts.values():
        filter_text_base_on_group_id_type = await TextUtils.filter_text_base_on_group_id_type_and_language_preference(texts=group_texts, language=language)
        root_text = filter_text_base_on_group_id_type[TextType.ROOT_TEXT.value]
        if root_text is None:
            continue
        recitation_text_list.append(RecitationDTO(text_id=root_text.id, title=root_text.title))
    return RecitationsResponse(recitations=recitation_text_list)


def _group_texts_by_group_id(texts: List[TextDTO], language: str|None = None) -> Dict[str, List[TextDTO]]:
    texts_by_group_id = {}
    for text in texts:
        group_id = str(text.group_id)
        if group_id not in texts_by_group_id:
            texts_by_group_id[group_id] = []
        texts_by_group_id[group_id].append(text)
    
    # Sort texts within each group by language preference
    for group_id in texts_by_group_id:
        texts_by_group_id[group_id].sort(
            key=lambda text: TextUtils.get_language_priority(text.language, language)
        )

    return texts_by_group_id


async def _get_texts_by_collection_id(collection_id: str, language: str, skip: int, limit: int) -> Tuple[List[TextDTO], int]:
    texts = await get_all_texts_by_collection(collection_id=collection_id)
    group_id_set = set()
    for text in texts:
        group_id_set.add(text.group_id) 
    total_unique_group_ids = len(group_id_set)
    texts.sort(
                key=lambda text: TextUtils.get_language_priority(text.language, language)
            )
    track_skip = 0
    track_limit = 0
    text_list = []
    visited_group_ids = set()
    for text in texts:
        if text.group_id in visited_group_ids:
            continue
        elif track_skip < skip:
            track_skip += 1
            continue
        if text is not None:
            text_list.append(TextDTO(
                id=str(text.id),
                pecha_text_id=str(text.pecha_text_id),
                title=text.title,
                language=text.language,
                group_id=text.group_id,
                type="root_text",
                is_published=text.is_published,
                created_date=text.created_date,
                updated_date=text.updated_date,
                published_date=text.published_date,
                published_by=text.published_by,
            ))
        track_limit += 1
        if track_limit >= limit:
            break;
        visited_group_ids.add(text.group_id)
    return text_list, total_unique_group_ids


async def _get_table_of_content_by_version_text_id(versions: List[TextDTO]) -> Dict[str, List[str]]:
    versions_table_of_content_id_dict = {}
    for version in versions:
        list_of_table_of_contents = await get_contents_by_id(text_id=str(version.id))
        list_of_table_of_contents_ids = []
        for table_of_content in list_of_table_of_contents:
            list_of_table_of_contents_ids.append(str(table_of_content.id))
        versions_table_of_content_id_dict[str(version.id)] = list_of_table_of_contents_ids
    return versions_table_of_content_id_dict


async def get_commentaries_by_text_id(text_id: str, skip: int, limit: int) -> List[TextDTO]:
    is_valid_text = await TextUtils.validate_text_exists(text_id=text_id)
    if not is_valid_text:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE)
    
    root_text = await TextUtils.get_text_detail_by_id(text_id=text_id)
    group_id = root_text.group_id

    commentaries = await TextUtils.get_commentaries_by_text_type(text_type="commentary", language=root_text.language, skip=skip, limit=limit)
    final_commentary = []
    for commentary in commentaries:
        if commentary.categories and group_id in commentary.categories:
            final_commentary.append(commentary)
    return final_commentary


def _get_list_of_text_version_response_model(versions: List[TextDTO], versions_table_of_content_id_dict: Dict[str, List[str]]) -> List[TextVersion]:
    list_of_version = [
        TextVersion(
            id=str(version.id),
            title=version.title,
            language=version.language,
            type=version.type,
            group_id=version.group_id,
            table_of_contents=versions_table_of_content_id_dict.get(str(version.id), []),
            is_published=version.is_published,
            created_date=version.created_date,
            updated_date=version.updated_date,
            published_date=version.published_date,
            published_by=version.published_by,
            source_link=version.source_link,
            ranking=version.ranking,
            license=version.license
        )
        for version in versions
    ]
    return list_of_version

async def update_text_details(text_id: str, update_text_request: UpdateTextRequest):
    is_valid_text = await TextUtils.validate_text_exists(text_id=text_id)
    if not is_valid_text:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE)
    text_details = await TextUtils.get_text_detail_by_id(text_id=text_id)
    text_details.updated_date = Utils.get_utc_date_time()
    text_details.title = update_text_request.title
    text_details.is_published = update_text_request.is_published
    
    # Update the text details in the database
    updated_text = await update_text_details_by_id(text_id=text_id, update_text_request=update_text_request)
    
    # Update the cache with the new text details
    try:
        await update_text_details_cache(text_id=text_id, updated_text_data=updated_text)
    except Exception as e:
        # If cache update fails, log the error but don't fail the entire operation
        # Fallback to cache invalidation to ensure consistency
        logging.error(f"Failed to update cache for text_id {text_id}: {str(e)}")
        await invalidate_text_cache_on_update(text_id=text_id)
    
    return updated_text

async def delete_text_by_text_id(text_id: str):
    is_valid_text = await TextUtils.validate_text_exists(text_id=text_id)
    if not is_valid_text:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE)
    await delete_text_by_id(text_id=text_id)


def _filter_single_section_(section: Section, wanted_segment_ids: Set[str]) -> Section | None:
    kept_segments = []
    for segment in section.segments:
        if segment.segment_id in wanted_segment_ids:
            kept_segments.append(segment)
    
    kept_subsections = []
    if section.sections:
        for subsection in section.sections:
            filtered_subsection = _filter_single_section_(subsection, wanted_segment_ids)
            if filtered_subsection is not None:
                kept_subsections.append(filtered_subsection)
    
    has_wanted_segments = len(kept_segments) > 0
    has_valid_subsections = len(kept_subsections) > 0
    
    if has_wanted_segments or has_valid_subsections:
        new_section = Section(
            id=section.id,
            title=section.title,
            section_number=section.section_number,
            parent_id=section.parent_id,
            segments=kept_segments,
            sections=kept_subsections if kept_subsections else None,
            created_date=section.created_date,
            updated_date=section.updated_date,
            published_date=section.published_date
        )
        return new_section
    else:
        return None

def _generate_paginated_table_of_content_by_segments_(
    table_of_content: TableOfContent,
    segment_dict: Dict[str, int]
) -> TableOfContent:

    wanted_segment_ids = set(segment_dict.keys())
    
    filtered_sections = []
    for section in table_of_content.sections:
        filtered_section = _filter_single_section_(section=section, wanted_segment_ids=wanted_segment_ids)
        if filtered_section is not None:
            filtered_sections.append(filtered_section)
    
    paginated_table_of_content = TableOfContent(
        id=str(table_of_content.id),
        text_id=table_of_content.text_id,
        type=table_of_content.type,
        sections=filtered_sections
    )
    
    return paginated_table_of_content


def _get_trimmed_segment_dict_(segments_with_position:List[Tuple[str,int]], segment_id: str, direction: PaginationDirection, size: int) -> Dict[str, int]:
    

    dict_segment_id_with_position: Dict[str, int] = dict(segments_with_position)

    segment_position = dict_segment_id_with_position.get(segment_id) - 1

    total_segments = len(segments_with_position)

    if direction == PaginationDirection.NEXT:
        trimmed_segments_with_position = segments_with_position[segment_position : min(segment_position + size, total_segments)]

    else:
        trimmed_segments_with_position = segments_with_position[max(0, segment_position - size + 1) : segment_position + 1]
    
    trimmed_segments_with_position = dict(trimmed_segments_with_position)

    return trimmed_segments_with_position

def _get_segments_with_position_(table_of_content: TableOfContent) -> List[Tuple[str, int]]:
    segments_with_position: List[Tuple[str, int]] = []
    position = 1
    
    def get_segment_from_section(section: Section):
        nonlocal position
        
        for segment in section.segments:
            segments_with_position.append((segment.segment_id, position))
            position += 1
        
        if section.sections:
            for sub_section in section.sections: 
                get_segment_from_section(sub_section)
    
    for section in table_of_content.sections:
        get_segment_from_section(section)
    return segments_with_position


async def _receive_table_of_content(text_id: str, text_details_request: TextDetailsRequest) -> TableOfContent:
    table_of_content = None
    if text_details_request.content_id is not None and text_details_request.segment_id is not None:
        table_of_content:TableOfContent = await get_table_of_content_by_content_id(
            content_id=text_details_request.content_id
        )
    elif text_details_request.segment_id is not None:
        table_of_contents: List[TableOfContent] = await get_contents_by_id(text_id=text_id)
        table_of_content: TableOfContent = _search_table_of_content_where_segment_id_exists(table_of_contents=table_of_contents, segment_id=text_details_request.segment_id)
    else:
        table_of_content = await get_contents_by_id(text_id=text_id)
        segment_id, table_of_content = _get_first_segment_and_table_of_content_(table_of_contents=table_of_content)
        text_details_request.segment_id = segment_id

    if table_of_content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorConstants.TABLE_OF_CONTENT_NOT_FOUND_MESSAGE
        )
    return table_of_content

def _get_first_segment_and_table_of_content_(table_of_contents: List[TableOfContent]) -> tuple[str | None, TableOfContent | None]:
    def find_first_segment(sections: list) -> str | None:
        for section in sections:
            if section.segments:
                return section.segments[0].segment_id
            if section.sections:
                result = find_first_segment(section.sections)
                if result:
                    return result
        return None

    for table_of_content in table_of_contents:
        segment_id = find_first_segment(sections=table_of_content.sections)
        if segment_id:
            return segment_id, table_of_content
    return None, None

def _search_section_(sections: List[Section], segment_id: str) -> bool:
    for section in sections:
        for segment in section.segments:
            if segment.segment_id == segment_id:
                return True
        
        if section.sections:
            result = _search_section_(sections=section.sections, segment_id=segment_id)
            if result:  
                return result
    
    return False

def _search_table_of_content_where_segment_id_exists(table_of_contents: List[TableOfContent], segment_id: str) -> TableOfContent:
    for table_of_content in table_of_contents:
        result = _search_section_(sections=table_of_content.sections, segment_id=segment_id)
        if result:
            return table_of_content
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorConstants.TABLE_OF_CONTENT_NOT_FOUND_MESSAGE
    )   

async def get_text_by_pecha_text_ids_service(texts_by_pecha_text_ids_request: TextsByPechaTextIdsRequest) -> Optional[List[TextDTO]]:
    pecha_text_ids = texts_by_pecha_text_ids_request.pecha_text_ids
    texts = await get_texts_by_pecha_text_ids(pecha_text_ids=pecha_text_ids)
    return [TextDTO(
        id=str(text.id),
        pecha_text_id=str(text.pecha_text_id),
        title=text.title,
        language=text.language,
        group_id=text.group_id,
        type=text.type,
        is_published=text.is_published,
        created_date=text.created_date,
        updated_date=text.updated_date,
        published_date=text.published_date,
        published_by=text.published_by,
        categories=text.categories,
        views=text.views,
        source_link=text.source_link,
        ranking=text.ranking,
        license=text.license
    ) for text in texts]