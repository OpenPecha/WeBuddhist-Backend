from typing import Annotated

from fastapi import APIRouter, Query
from starlette import status

from .segments_openpecha_service import (
    get_commentaries_by_segment_id_from_openpecha,
    get_translations_by_segment_id_from_openpecha,
)
from .segments_response_models import (
    V2SegmentCommentariesResponse,
    V2SegmentTranslationsResponse,
)

segments_v2_router = APIRouter(
    prefix="/v2/segments",
    tags=["segments-v2"],
)


@segments_v2_router.get(
    "/{segment_id}/translations",
    status_code=status.HTTP_200_OK,
    summary="Get translations for a segment from OpenPecha",
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
    summary="Get commentaries for a segment from OpenPecha",
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
