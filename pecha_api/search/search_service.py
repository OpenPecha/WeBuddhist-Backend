from elastic_transport import ObjectApiResponse
from fastapi import HTTPException
from starlette import status

from pecha_api.plans.response_message import NO_SEGMENTATION_IDS_RETURNED
from .search_enums import SearchType
from .search_client import search_client
from pecha_api.config import get
from typing import List, Dict, Optional
from pecha_api.texts.segments.segments_models import Segment
from pecha_api.texts.texts_models import Text

from pecha_api.http_message_utils import handle_http_status_error, handle_request_error
import httpx
import logging
from .search_response_models import (
    SearchResponse,
    TextIndex,
    SegmentMatch,
    SourceResultItem,
    Search,
    SheetResultItem,
    ExternalSearchResponse,
    MultilingualSegmentMatch,
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



def build_language_filter(language: str) -> List[str]:
    if language == "bo":
        return ["bo", "tib"]
    return [language]


def build_search_filter(title: Optional[str] = None, language: Optional[str] = None) -> Dict[str, List[str]]:
    filter_obj = {}
    
    if language:
        filter_obj["language"] = build_language_filter(language)
    
    if title:
        filter_obj["title"] = [title]
    
    return filter_obj


def build_search_payload(
    query: str,
    search_type: str,
    limit: int,
    title: Optional[str] = None,
    language: Optional[str] = None
) -> Dict:
    payload = {
        "query": query,
        "search_type": search_type,
        "limit": limit,
        "return_text": False,
        "hierarchical": True,
    }
    
    if language or title:
        payload["filter"] = build_search_filter(title, language)
    
    return payload


def group_segments_by_text(segments: List[Segment]) -> Dict[str, List[Segment]]:
    text_segments_map: Dict[str, List[Segment]] = {}
    for segment in segments:
        if segment.text_id not in text_segments_map:
            text_segments_map[segment.text_id] = []
        text_segments_map[segment.text_id].append(segment)
    return text_segments_map


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


def build_segment_matches(segments: List[Segment], results_map: Dict[str, Dict]) -> List[MultilingualSegmentMatch]:
    segment_matches = []
    for segment in segments:
        pecha_id = segment.pecha_segment_id
        if pecha_id and pecha_id in results_map:
            segment_matches.append(
                MultilingualSegmentMatch(
                    segment_id=str(segment.id),
                    content=segment.content,
                    relevance_score=results_map[pecha_id]["distance"],
                    pecha_segment_id=pecha_id
                )
            )
    segment_matches.sort(key=lambda x: x.relevance_score)
    return segment_matches


async def get_text_title_by_id(text_id: Optional[str]) -> Optional[str]:
    if not text_id:
        return None
    
    text = await Text.get_text(text_id)
    if text:
        return text.title
    
    return None


def build_results_map(external_results: ExternalSearchResponse) -> tuple[List[str], Dict[str, Dict]]:
    segmentation_ids = []
    results_map = {}
    
    for result in external_results.results:
        if result.id:
            segmentation_ids.append(result.id)
            results_map[result.id] = {
                "distance": result.distance,
                "content": result.entity.text if result.entity.text else ""
            }
    
    return segmentation_ids, results_map


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


async def get_multilingual_search_results(
    query: str,
    search_type: str = "hybrid",
    text_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    language: Optional[str] = None
) -> MultilingualSearchResponse:
    try:
        title = await get_text_title_by_id(text_id)
        
        external_limit = min(limit * 5, 100)
        
        external_results = await call_external_search_api(
            query=query,
            search_type=search_type,
            limit=external_limit,
            title=title,
            language=language
        )
        
        segmentation_ids, results_map = build_results_map(external_results)
        
        if not segmentation_ids:
            logger.info(NO_SEGMENTATION_IDS_RETURNED)
            return create_empty_search_response(query, search_type, skip, limit)
        
        segments = await fetch_segments_by_ids(segmentation_ids, text_id)
        
        if not segments:
            return create_empty_search_response(query, search_type, skip, limit)
        
        final_display_sources = await build_multilingual_sources(segments, results_map)
        
        paginated_sources = apply_pagination_to_sources(final_display_sources, skip, limit)
        
        return MultilingualSearchResponse(
            query=query,
            search_type=search_type,
            sources=paginated_sources,
            skip=skip,
            limit=limit,
            total=limit
        )
        
    except Exception as e:
        logger.error(f"Error in multilingual search: {str(e)}", exc_info=True)
        raise


async def call_external_search_api(
    query: str,
    search_type: str = "hybrid",
    limit: int = 10,
    title: Optional[str] = None,
    language: Optional[str] = None
) -> ExternalSearchResponse:

    external_api_url = "https://search.buddhistai.tools"
    endpoint = f"{external_api_url}/search"
    
    payload = build_search_payload(query, search_type, limit, title, language)
    print(payload)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            data = response.json()
            return ExternalSearchResponse(**data)
            
    except httpx.HTTPStatusError as e:
        handle_http_status_error(e)
    except httpx.RequestError as e:
        handle_request_error(e)



async def build_multilingual_sources(segments: List[Segment], results_map: Dict[str, Dict]) -> List[MultilingualSourceResult]:
    text_segments_map = group_segments_by_text(segments)
    text_info_map = await fetch_text_info(list(text_segments_map.keys()))
    
    sources = []
    for text_id, text_segments in text_segments_map.items():
        if text_id not in text_info_map:
            continue
        
        segment_matches = build_segment_matches(text_segments, results_map)
        
        sources.append(
            MultilingualSourceResult(
                text=text_info_map[text_id],
                segment_matches=segment_matches
            )
        )
    
    return sources

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