from typing import Annotated, Optional

from fastapi import APIRouter, Query
from starlette import status

from .segments_openpecha_service import (
    get_commentaries_by_segment_id_from_openpecha,
    get_openpecha_segment_details_by_id,
    get_root_text_by_segment_id_from_openpecha,
    get_translations_by_segment_id_from_openpecha,
)
from .segments_response_models import (
    V2SegmentCommentariesResponse,
    V2SegmentResponse,
    V2SegmentTranslationsResponse,
    V2SegmentRootTextResponse,
)

segments_v2_router = APIRouter(
    prefix="/v2/segments", #lets remove the v2 once migration is done
    tags=["Segments"],
)

@segments_v2_router.get("/{segment_id}", status_code=status.HTTP_200_OK)
async def get_segment_v2(
    segment_id: str,
    text_id: Annotated[Optional[str], Query()] = None,
) -> V2SegmentResponse:
    return await get_openpecha_segment_details_by_id(
        segment_id=segment_id,
        text_id=text_id,
    )

@segments_v2_router.get(
    "/{segment_id}/root_text",
    status_code=status.HTTP_200_OK,
    summary="Get Root Text for Segment",
)
async def get_root_text_for_segment_v2(
    text_id: str,
    segment_id: str,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> V2SegmentRootTextResponse:
    return await get_root_text_by_segment_id_from_openpecha(
        text_id=text_id,
        segment_id=segment_id,
        skip=skip,
        limit=limit,
    )

@segments_v2_router.get(
    "/{segment_id}/translations",
    status_code=status.HTTP_200_OK,
    summary="Get Translations for Segment",
)
async def get_translations_for_segment_v2(
    segment_id: str,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> V2SegmentTranslationsResponse:
    return await get_translations_by_segment_id_from_openpecha(
        segment_id=segment_id,
        skip=skip,
        limit=limit,
    )


@segments_v2_router.get(
    "/{segment_id}/commentaries",
    status_code=status.HTTP_200_OK,
    summary="Get Commentaries for Segment",
)
async def get_commentaries_for_segment_v2(
    segment_id: str,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> V2SegmentCommentariesResponse:
    return await get_commentaries_by_segment_id_from_openpecha(
        segment_id=segment_id,
        skip=skip,
        limit=limit,
    )
