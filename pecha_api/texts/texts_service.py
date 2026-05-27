from fastapi import HTTPException
from starlette import status

from pecha_api.error_contants import ErrorConstants
from .texts_repository import (
    create_table_of_content_detail,
    get_contents_by_id,
    delete_table_of_content_by_text_id,
    update_text_details_by_id,
    delete_text_by_id,
    fetch_sheets_from_db,
    get_all_recitation_texts_by_collection,
    get_texts_by_pecha_text_ids,
)
from .texts_response_models import (
    TableOfContent,
    TableOfContentType,
    TextDTO,
    TextSegment,
    Section,
    UpdateTextRequest,
    TextsByPechaTextIdsRequest,
)

from pecha_api.recitations.recitations_response_models import (
    RecitationDTO,
    RecitationsResponse
)

from pecha_api.texts.texts_cache_service import (
    get_table_of_content_by_sheet_id_cache,
    set_table_of_content_by_sheet_id_cache,
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
from .segments.segments_utils import SegmentUtils

from typing import List, Dict, Optional
from pecha_api.utils import Utils
from .texts_enums import TextType

import logging


async def get_sheet(
    published_by: Optional[str] = None,
    is_published: Optional[bool] = None,
    sort_by: Optional[SortBy] = None,
    sort_order: Optional[SortOrder] = None,
    skip: int = 0,
    limit: int = 10
):
    return await fetch_sheets_from_db(
        published_by=published_by,
        is_published=is_published,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit
    )


async def get_table_of_content_by_sheet_id(sheet_id: str) -> Optional[TableOfContent]:
    cached_data: TableOfContent = await get_table_of_content_by_sheet_id_cache(
        sheet_id=sheet_id, cache_type=CacheType.SHEET_TABLE_OF_CONTENT
    )
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
        await set_table_of_content_by_sheet_id_cache(
            sheet_id=sheet_id, cache_type=CacheType.SHEET_TABLE_OF_CONTENT, data=table_of_content
        )

    return table_of_content


async def remove_table_of_content_by_text_id(text_id: str):
    is_valid_text = await TextUtils.validate_text_exists(text_id=text_id)
    if not is_valid_text:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE)
    return await delete_table_of_content_by_text_id(text_id=text_id)


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


async def get_root_text_by_collection_id(collection_id: str, language: str) -> Optional[tuple[str, str]]:
    texts = await get_all_recitation_texts_by_collection(collection_id=collection_id, language=language)
    grouped_texts = _group_texts_by_group_id(texts=texts, language=language)
    recitation_text_list = []
    for group_texts in grouped_texts.values():
        filter_text_base_on_group_id_type = await TextUtils.filter_text_base_on_group_id_type_and_language_preference(
            texts=group_texts, language=language
        )
        root_text = filter_text_base_on_group_id_type[TextType.ROOT_TEXT.value]
        if root_text is None:
            continue
        recitation_text_list.append(RecitationDTO(text_id=root_text.id, title=root_text.title))
    return RecitationsResponse(recitations=recitation_text_list)


async def update_text_details(text_id: str, update_text_request: UpdateTextRequest):
    is_valid_text = await TextUtils.validate_text_exists(text_id=text_id)
    if not is_valid_text:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE)
    text_details = await TextUtils.get_text_detail_by_id(text_id=text_id)
    text_details.updated_date = Utils.get_utc_date_time()
    text_details.title = update_text_request.title
    text_details.is_published = update_text_request.is_published

    updated_text = await update_text_details_by_id(text_id=text_id, update_text_request=update_text_request)

    try:
        await update_text_details_cache(text_id=text_id, updated_text_data=updated_text)
    except Exception as e:
        logging.exception(f"Failed to update cache for text_id {text_id}")
        await invalidate_text_cache_on_update(text_id=text_id)

    return updated_text


async def delete_text_by_text_id(text_id: str):
    is_valid_text = await TextUtils.validate_text_exists(text_id=text_id)
    if not is_valid_text:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE)
    await delete_text_by_id(text_id=text_id)


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


# PRIVATE FUNCTIONS

async def get_table_of_content_by_type(table_of_content: TableOfContent):
    if table_of_content.type == TableOfContentType.TEXT:
        return await replace_pecha_segment_id_with_segment_id(table_of_content=table_of_content)
    return table_of_content


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
        new_segments = [
            TextSegment(
                segment_id=str(segments_dict[segment.segment_id]),
                segment_number=segment.segment_number
            )
            for segment in section.segments
        ]
        new_section = Section(
            id=section.id,
            title=section.title,
            section_number=section.section_number,
            segments=new_segments
        )
        new_sections.append(new_section)
    new_toc.sections = new_sections
    return new_toc


def _group_texts_by_group_id(texts: List[TextDTO], language: str | None = None) -> Dict[str, List[TextDTO]]:
    texts_by_group_id: Dict[str, List[TextDTO]] = {}
    for text in texts:
        group_id = str(text.group_id)
        if group_id not in texts_by_group_id:
            texts_by_group_id[group_id] = []
        texts_by_group_id[group_id].append(text)

    for group_id in texts_by_group_id:
        texts_by_group_id[group_id].sort(
            key=lambda text: TextUtils.get_language_priority(text.language, language)
        )

    return texts_by_group_id
