from fastapi.security import HTTPBearer
from fastapi import APIRouter
from starlette import status

from .segments_service import (
    get_translations_by_segment_id,
    get_commentaries_by_segment_id,
    get_segment_details_by_id, 
    get_info_by_segment_id,
    get_root_text_mapping_by_segment_id,
    search_segments_by_content_service,
)
from .segments_response_models import (
    SegmentDTO,
    SegmentResponse,
    SegmentInfoResponse,
    SegmentTranslationsResponse,
    SegmentCommentariesResponse,
    SegmentSearchRequest,
)

oauth2_scheme = HTTPBearer()
segment_router = APIRouter(
    prefix="/segments",
    tags=["Segments"]
)

from fastapi import Query


@segment_router.post("/search", status_code=status.HTTP_200_OK, deprecated=True)
async def search_segments(
    segment_search_request: SegmentSearchRequest,
) -> SegmentResponse:
    return await search_segments_by_content_service(
        segment_search_request=segment_search_request,
    )


@segment_router.get("/{segment_id}", status_code=status.HTTP_200_OK)
async def get_segment(
    segment_id: str,
    text_details: bool = Query(default=False)
) -> SegmentDTO:
    return await get_segment_details_by_id(segment_id=segment_id, text_details=text_details)


@segment_router.get("/{segment_id}/info", status_code=status.HTTP_200_OK)
async def get_info_for_segment(
    segment_id: str
) -> SegmentInfoResponse:
    return await get_info_by_segment_id(segment_id=segment_id)


@segment_router.get("/{segment_id}/root_text", status_code=status.HTTP_200_OK)
async def get_root_text_for_segment(
    segment_id: str
):
    return await get_root_text_mapping_by_segment_id(segment_id=segment_id)


@segment_router.get("/{segment_id}/translations", status_code=status.HTTP_200_OK)
async def get_translations_for_segment(
    segment_id: str
) -> SegmentTranslationsResponse:
    return await get_translations_by_segment_id(
        segment_id=segment_id
    )


@segment_router.get("/{segment_id}/commentaries", status_code=status.HTTP_200_OK)
async def get_commentaries_for_segment(
    segment_id: str
) -> SegmentCommentariesResponse:
    return await get_commentaries_by_segment_id(
        segment_id=segment_id
    )