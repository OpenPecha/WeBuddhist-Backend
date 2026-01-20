import logging
from typing import Any, List
from pecha_api.text_uploader.segments.segment_respository import (
    get_segments_annotation,
    post_segments,
    get_segments_id_by_annotation_id,
    get_segments_by_id
)

from pecha_api.texts.segments.segments_repository import get_segments_by_text_id
from pecha_api.text_uploader.text_uploader_response_model import TextUploadRequest

logging.basicConfig(level=logging.INFO)

class SegmentService:

    async def upload_segments(self, text_upload_request: TextUploadRequest, text_ids: dict[str, Any], token: str):

        try:
            for text_id, pecha_text_id in text_ids.items():

                if await self.is_text_segments_uploaded(text_id):
                    print(f"Segments for text_id {pecha_text_id} already uploaded. Skipping...")
                    continue

                instance = await self.get_segments_annotation_by_pecha_text_id(text_upload_request, pecha_text_id)
                annotation_ids = self.get_annotation_ids(instance)
                annotation_sengments = await get_segments_id_by_annotation_id(annotation_ids[0], text_upload_request.openpecha_api_url)
                segments_ids = [segment["id"] for segment in annotation_sengments["data"]]
                # Process segment_ids in batches to manage batch size
                
                # segments_contents = await self.make_batch_segments_content(segments_ids, pecha_text_id)
                segments_contents = self.parse_segments_content(annotation_sengments["data"], instance['content'])

                await self.upload_bulk_segments(text_id, segments_contents,text_upload_request, token)
        except Exception as e:
            print("Error: ", e)


    def parse_segments_content(self, segments_annotation: List[dict[str, Any]], base_text: str) -> List[dict[str, Any]]:
        segments_content = []
        for segment in segments_annotation:
            segment_content = base_text[segment["span"]["start"]:segment["span"]["end"]]
            segments_content.append({
                "segment_id": segment["id"],
                "content": segment_content
            })
        return segments_content


    async def upload_bulk_segments(self, text_id: str, segments_content: List[dict[str, Any]], text_upload_request, token: str) -> List[dict[str, Any]]:
        """
        Create and post segments in batches to avoid payload size limits.
        """
        batch_size = 400  # Adjust batch size as needed
        total_segments = len(segments_content)

        print(f"\nPosting {total_segments} segments in batches of {batch_size}...\n")
        
        for i in range(0, total_segments, batch_size):
            batch = segments_content[i:i + batch_size]
            batch_number = (i // batch_size) + 1
            total_batches = (total_segments + batch_size - 1) // batch_size
            
            payload = {
                "text_id": text_id,
                "segments": [
                    {
                        "pecha_segment_id": segment["segment_id"],
                        "content": segment["content"],
                        "type": "source",
                    } for segment in batch
                ]
            }
            
            logging.info(f"Posting batch {batch_number}/{total_batches} ({len(batch)} segments)...\n")
            await post_segments(payload, text_upload_request.destination_url, token)

    async def get_segments_annotation_by_pecha_text_id(
        self, text_upload_request: TextUploadRequest, pecha_text_id: str
    ) -> dict[str, Any]:
        return await get_segments_annotation(pecha_text_id, text_upload_request.openpecha_api_url)


    def get_annotation_ids(self, instance: dict[str, Any]) -> list[str]:
        annotations = instance["annotations"] or []
        segmentation_ids: list[str] = []
        for annotation in annotations:
            if annotation["type"] == "segmentation":
                segmentation_ids.append(annotation["annotation_id"])
        return segmentation_ids


    async def is_text_segments_uploaded(self, text_id: str) -> bool:
        segments = await get_segments_by_text_id(text_id)
        return len(segments) > 0


    async def get_segments_by_id_list(self, annotation_ids: str, text_upload_request: TextUploadRequest) -> List[dict[str, Any]]:
        
        segments = await get_segments_by_id(annotation_ids, text_upload_request.openpecha_api_url)
        return segments

