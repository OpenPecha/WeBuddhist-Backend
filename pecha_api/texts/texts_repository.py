from __future__ import annotations

import logging
from typing import List, Optional, Dict
from uuid import UUID

from beanie.exceptions import CollectionWasNotInitialized
from pecha_api.constants import Constants
from .texts_response_models import (
    TableOfContent,
    TextDTO,
)
from .texts_models import Text, TableOfContent

async def get_texts_by_id(text_id: str) -> Text | None:
    try:
        text = await Text.get_text(text_id=text_id)
        return text
    except CollectionWasNotInitialized as e:
        logging.debug(e)
        return None

async def get_texts_by_ids(text_ids: List[str]) -> Dict[str, TextDTO]:
    list_of_texts_detail = await Text.get_texts_by_ids(text_ids=text_ids)
    return {
        str(text.id): TextDTO(
            id=str(text.id),
            pecha_text_id=str(text.pecha_text_id),
            title=text.title,
            language=text.language,
            type=text.type,
            group_id=text.group_id,
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
        )
        for text in list_of_texts_detail
    }

async def check_text_exists(text_id: UUID) -> bool:
    try:
        is_text_exits = await Text.check_exists(text_id=text_id)
        return is_text_exits
    except CollectionWasNotInitialized as e:
        logging.debug(e)
        return False

async def check_all_text_exists(text_ids: List[UUID]) -> bool:
    try:
        is_text_exits = await Text.exists_all(text_ids=text_ids,batch_size=Constants.QUERY_BATCH_SIZE)
        return is_text_exits
    except CollectionWasNotInitialized as e:
        logging.debug(e)
        return False

async def get_texts_by_titles(titles: List[str]) -> List[Text]:
    if not titles:
        return []
    return await Text.find({"title": {"$in": titles}}).to_list()

async def get_contents_by_id(text_id: str) -> List[TableOfContent]:
    return await TableOfContent.get_table_of_contents_by_text_id(text_id=text_id)
    
async def get_table_of_content_by_content_id(content_id: str, skip: int = None, limit: int = None) -> Optional[TableOfContent]:
    return await TableOfContent.get_table_of_content_by_content_id(content_id=content_id, skip=skip, limit=limit)