from elastic_transport import ObjectApiResponse
from fastapi import HTTPException
from starlette import status

from .search_enums import SearchType
from .search_client import search_client
from pecha_api.config import get
from typing import List, Dict, Optional
from pecha_api.texts.segments.segments_models import Segment
from pecha_api.texts.texts_models import Text

import logging
from .search_response_models import (
    SearchResponse,
    TextIndex,
    SegmentMatch,
    SourceResultItem,
    Search,
    SheetResultItem,
    MultilingualSourceResult,
    MultilingualSearchResponse,
    SegmentLinkResponse,
)

logger = logging.getLogger(__name__)

MAX_SEARCH_LIMIT = 30

async def get_search_results(query: str, search_type: SearchType, text_id: str = None, skip: int = 0, limit: int = 10) -> SearchResponse:

    if SearchType.SOURCE == search_type:
        response: SearchResponse = await _source_search(
            query=query,
            text_id=text_id,
            skip=skip,
            limit=limit
        )

    elif SearchType.SHEET == search_type:
        response: SearchResponse = _sheet_search(
            query=query,
            skip=skip,
            limit=limit
        )
    
    return response


async def _source_search(
        query: str, 
        text_id: str, 
        skip: int, 
        limit: int
) -> SearchResponse:
    client = search_client()
    search_query = _generate_search_query(
        query=query,
        text_id=text_id,
        skip=skip,
        limit=limit
    )
    query_response: ObjectApiResponse = await client.search(
        index=get("ELASTICSEARCH_SEGMENT_INDEX"),
        **search_query
    )
    search_response: SearchResponse = _process_source_search_response(
        query, 
        query_response, 
        skip, 
        limit)
    return search_response


def _process_source_search_response(query: str, search_response: ObjectApiResponse, skip: int, limit: int) -> SearchResponse:
    hits = search_response["hits"]["hits"]
    total = search_response["hits"]["total"]["value"] if "total" in search_response["hits"] else 0
    source_dict, text_dict = _group_sources_by_text_id(hits=hits)
    sources: List[SourceResultItem] = _get_source_result_items_(text_dict=text_dict, source_dict=source_dict)
    return SearchResponse(
        search=Search(
            text=query,
            type=SearchType.SOURCE
        ),
        sources=sources,
        skip=skip,
        limit=limit,
        total=min(MAX_SEARCH_LIMIT, total)
    )

def _get_source_result_items_(text_dict: dict, source_dict: dict) -> List[SourceResultItem]:
    sources: List[SourceResultItem] = []
    for source_key in source_dict.keys():
        text = TextIndex(
            text_id=text_dict[source_key].text_id,
            language=text_dict[source_key].language,
            title=text_dict[source_key].title,
            published_date=text_dict[source_key].published_date
        )
        segment_matches: List[SegmentMatch] = []
        for data in source_dict[source_key]:
            segment_matches.append(
                SegmentMatch(
                    segment_id=data["id"],
                    content=data["content"]
                )
            )
        sources.append(
            SourceResultItem(
                text=text,
                segment_match=segment_matches
            )
        )
    return sources

def _group_sources_by_text_id(hits: list) -> tuple[dict, dict]:
    source_dict = {}
    text_dict = {}
    for result in hits:
        source = result["_source"]
        text = source["text"]
        text_id = source["text_id"]
        text_index = TextIndex(
            text_id=text_id,
            language=text["language"],
            title=text["title"],
            published_date=text["published_date"]
        )
        if text_id not in source_dict:
            source_dict[text_id] = [source]
            text_dict[text_id] = text_index
        else:
            source_dict[text_id].append(source)
    return source_dict, text_dict

def _generate_search_query(
        query: str, 
        text_id: str, 
        skip: int, 
        limit: int
):
    search_query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "content": {
                                "query": query
                            }
                        }
                    }
                ]
            }
        },
        "from": skip,
        "size": limit
    }
    if text_id:
        search_query["query"]["bool"]["must"].append({
            "term": {
                "text_id.keyword": text_id
            }
        })
    return search_query

def _sheet_search(query: str, skip: int, limit: int) -> SearchResponse:
    return SearchResponse(
        search=Search(
            text=query,
            type=SearchType.SHEET
        ),
        sheets=[],
        skip=skip,
        limit=limit,
        total=0
    )



async def fetch_text_info(text_ids: List[str]) -> Dict[str, TextIndex]:
    text_info_map: Dict[str, TextIndex] = {}
    for text_id in text_ids:
        text = await Text.get_text(text_id)
        if text:
            text_info_map[text_id] = TextIndex(
                text_id=text_id,
                language=text.language,
                title=text.title,
                published_date=str(text.created_at) if hasattr(text, 'created_at') else ""
            )
    return text_info_map


def create_empty_search_response(
    query: str,
    search_type: str,
    skip: int,
    limit: int
) -> MultilingualSearchResponse:
    return MultilingualSearchResponse(
        query=query,
        search_type=search_type,
        sources=[],
        skip=skip,
        limit=limit,
        total=0
    )


def apply_pagination_to_sources(
    sources: List[MultilingualSourceResult],
    skip: int,
    limit: int
) -> List[MultilingualSourceResult]:

    all_matches = []
    for source in sources:
        for match in source.segment_matches:
            all_matches.append((source.text, match))
    
    all_matches.sort(key=lambda x: x[1].relevance_score)
    
    paginated_matches = all_matches[skip:skip + limit]
    
    text_to_matches: Dict[str, tuple] = {}
    for text_info, match in paginated_matches:
        text_key = text_info.text_id
        if text_key not in text_to_matches:
            text_to_matches[text_key] = (text_info, [])
        text_to_matches[text_key][1].append(match)
    
    paginated_sources = [
        MultilingualSourceResult(text=text_info, segment_matches=matches)
        for text_info, matches in text_to_matches.values()
    ]
    
    return paginated_sources


async def fetch_segments_by_ids(
    segmentation_ids: List[str],
    text_id: Optional[str]
) -> List[Segment]:
    segments = await Segment.get_segments_by_pecha_ids(
        pecha_segment_ids=segmentation_ids,
        text_id=text_id
    )
    
    if not segments:
        logger.warning(f"No internal segments found for {len(segmentation_ids)} segmentation IDs")
    
    return segments


async def get_url_link(pecha_segment_id: str) -> SegmentLinkResponse:
    try:
        segment = await Segment.get_segment_by_pecha_segment_id(pecha_segment_id=pecha_segment_id)

        if not segment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pecha segment not found")

        return SegmentLinkResponse(
            text_id=segment.text_id,
            segment_id=str(segment.id),
        )

    except HTTPException:
        raise
    except Exception:
        logger.error("Error generating URL for pecha segment", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve segment link")