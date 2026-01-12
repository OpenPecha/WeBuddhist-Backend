from typing import Any
import uuid
import logging

from pecha_api.text_uploader.segments.segment_service import SegmentService
from pecha_api.text_uploader.text_uploader_response_model import TextUploadRequest

from pecha_api.text_uploader.table_of_content.toc_repository import post_toc


logging.basicConfig(level=logging.INFO)

class TocService:
    def __init__(self):
        self.segment_service = SegmentService()

    async def upload_toc(self, text_ids: dict[str, Any], text_upload_request: TextUploadRequest, token: str):

        for text_id, pecha_text_id in text_ids.items():
            # Check if TOC already uploaded for this pecha_text_id
            
            instance = await self.segment_service.get_segments_annotation_by_pecha_text_id(text_upload_request, pecha_text_id)
            annotation_ids = self.segment_service.get_annotation_ids(instance)
            annotation_segments = await self.segment_service.get_segments_by_id_list(annotation_ids[0], text_upload_request)
            ordered_segments = await self.order_segments_by_annotation_span(annotation_segments)
            toc_payload = self.create_toc_payload(ordered_segments, text_id)
            
            
            await post_toc(toc_payload, text_upload_request.destination_url, token)
            logging.info(f'Table of Content  uploaded successfully for text_id: {text_id}')
            
        
    async def order_segments_by_annotation_span(self, annotation_segments: dict[str, Any]):

        segments_data = annotation_segments.get("data", [])
        sorted_segments = sorted(segments_data, key=lambda x: x["span"]["start"])
        result = [
            {"segment_id": segment["id"], "segment_number": idx + 1}
            for idx, segment in enumerate(sorted_segments)
        ]
        return result

    def create_toc_payload(self, ordered_segments: list[dict[str, Any]], text_id: str):
        section_id = str(uuid.uuid4())
        payload = {
            "text_id": text_id,
            "type": "text",
            "sections": [
                {
                    "id": section_id,
                    "title": "1",
                    "section_number": 1,
                    "segments": ordered_segments
                }
            ]
        }
        return payload
