from fastapi import HTTPException
from starlette import status
from pecha_api.texts.text_openpecha_response_models import TextDetailResponse, TextDetailRequest
from pecha_api.texts.texts_openpecha_api import fetch_critical_editions, fetch_text_detail, fetch_editions_segmentation, fetch_segmentation_segments, fetch_edition_content
from pecha_api.texts.text_openpecha_response_models import SegmentationSegmentResponseModel, SegmentContentModel, SegmentContentResponse    

async def get_text_detail_by_id(text_id: str, offset: int, limit: int) -> TextDetailResponse:
    # offset = text_detail_request.offset
    # limit = text_detail_request.limit
    text_detail = await fetch_text_detail(text_id=text_id)
    edition_details = await fetch_critical_editions(text_id=text_id)
    if not edition_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"No critical editions found for text with id '{text_id}'",
        )
    text_detail.edition_details = edition_details
    segmentations = await fetch_editions_segmentation(edition_id=edition_details[0].id)
    edition_content = await fetch_edition_content(edition_id=edition_details[0].id)
    segments = await fetch_segmentation_segments(segmentation_id=segmentations[0].id, limit=limit, offset=offset)  # noqa: F841
    segment_contents = trim_segment_content(edition_content=edition_content.content, segments=segments)
    text_detail.segments = segment_contents
    return text_detail


def trim_segment_content(edition_content: str, segments: SegmentationSegmentResponseModel) -> SegmentContentResponse:
    result = []
    for i, segment in enumerate(segments.items):
        content = "".join(edition_content[line.start:line.end] for line in segment.lines)
        result.append(SegmentContentModel(id=segment.id, content=content, segment_number=i+1))
    return SegmentContentResponse(contents=result, has_more=segments.has_more, offset=segments.offset, limit=segments.limit)



