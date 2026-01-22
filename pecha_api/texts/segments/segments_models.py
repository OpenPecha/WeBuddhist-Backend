from typing import List, Optional, Dict
import uuid
from pydantic import BaseModel, Field
from beanie import Document

from .segments_enum import SegmentType

class Mapping(BaseModel):
    text_id: str
    segments: List[str]


class Segment(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    pecha_segment_id: Optional[str] = None
    text_id: str
    content: str
    mapping: Optional[List[Mapping]] = None
    type: SegmentType

    class Settings:
        collection = "segments"
        indexes = [
            "mapping.segments"  # Index for faster lookup of segment IDs within mapping arrays
        ]

    @classmethod
    async def get_segments_by_pecha_segment_ids(cls, pecha_segment_ids: List[str]) -> List["Segment"]:
        pecha_segment_ids = [str(pecha_segment_id) for pecha_segment_id in pecha_segment_ids]
        return await cls.find({cls.pecha_segment_id: {"$in": pecha_segment_ids}}).to_list()

    @classmethod
    async def get_segment_by_id(cls, segment_id: str) -> Optional["Segment"]:
        return await cls.find_one(cls.id == uuid.UUID(segment_id))
    
    @classmethod
    async def update_segment_by_pecha_segment_id(cls, pecha_segment_id: str, content: str) -> Optional["Segment"]:
        return await cls.find_one(cls.pecha_segment_id == pecha_segment_id).update({"$set": {"content": content}})
    
    @classmethod
    async def get_segment_by_pecha_segment_id(cls, pecha_segment_id: str) -> Optional["Segment"]:
        return await cls.find_one(cls.pecha_segment_id == pecha_segment_id)
    @classmethod
    async def get_segments_by_ids(cls, segment_ids: List[str]) -> List["Segment"]:
        segment_ids = [uuid.UUID(segment_id) for segment_id in segment_ids]
        return await cls.find({"_id": {"$in": segment_ids}}).to_list()

    @classmethod
    async def get_segment_by_id_and_text_id(cls, segment_id: uuid.UUID, text_id: str) -> Optional["Segment"]:
        return await cls.find_one(cls.id == segment_id, cls.text_id == text_id)

    @classmethod
    async def get_segments_by_text_id(cls, text_id: str) -> List["Segment"]:
        return await cls.find(cls.text_id == text_id).to_list()

    @classmethod
    async def check_exists(cls, segment_id: uuid.UUID) -> bool:
        segment = await cls.find_one(cls.id == segment_id)
        return segment is not None

    
    @classmethod
    async def exists_all(cls, segment_ids: List[uuid.UUID], batch_size: int = 100) -> bool:
        if not segment_ids:
            return False
        found_segments = await cls.find({"_id": {"$in": segment_ids}}).to_list()
        found_ids = {segment.id for segment in found_segments}
        for segment_id in segment_ids:
            if segment_id not in found_ids:
                return False
        return True

    @classmethod
    async def get_segments_by_ids(cls, segment_ids: List[str]) -> List["Segment"]:
        segment_ids = [uuid.UUID(segment_id) for segment_id in segment_ids]
        return await cls.find({"_id": {"$in": segment_ids}}).to_list(length=len(segment_ids))
    @classmethod
    async def get_first_segment_by_ids_and_type(cls, segment_ids: List[str], segment_type: SegmentType) -> Optional["Segment"]:
        """Get the first segment matching the IDs and type - optimized for single result"""
        if not segment_ids:
            return None
        segment_uuid_ids = [uuid.UUID(segment_id) for segment_id in segment_ids]
        return await cls.find_one({"_id": {"$in": segment_uuid_ids}, "type": segment_type})

    @classmethod
    async def get_related_mapped_segments(cls, parent_segment_id: str) -> List["Segment"]:
        # Find segments where:
        # 1. There exists a mapping object with text_id matching parent_text_id
        # 2. Within that same mapping object, segments list contains parent_segment_id
        query = {
            "mapping": {
                "$elemMatch": {
                    "segments": {"$in": [parent_segment_id]}
                }
            }
        }
        return await cls.find(query).to_list()
    
    @classmethod
    async def get_segments_by_pecha_ids(
        cls, 
        pecha_segment_ids: List[str],
        text_id: Optional[str] = None
    ) -> List["Segment"]:

        query = {"pecha_segment_id": {"$in": pecha_segment_ids}}
        if text_id:
            query["text_id"] = text_id
        
        return await cls.find(query).to_list()

    @classmethod
    async def delete_segment_by_text_id(cls, text_id: str):
        return await cls.find(cls.text_id == text_id).delete()

    @classmethod
    async def get_related_mapped_segments_batch(
        cls, 
        parent_segment_ids: List[str],
        text_types: Optional[List[str]] = None
    ) -> Dict[str, List["Segment"]]:

        if not parent_segment_ids:
            return {}
        
        query = {
            "mapping": {
                "$elemMatch": {
                    "segments": {"$in": parent_segment_ids}
                }
            }
        }
        
        segments = await cls.find(query).to_list()
        
        result: Dict[str, List["Segment"]] = {pid: [] for pid in parent_segment_ids}
        
        for segment in segments:
            if segment.mapping:
                for mapping in segment.mapping:
                    for parent_id in parent_segment_ids:
                        if parent_id in mapping.segments:
                            if segment not in result[parent_id]:
                                result[parent_id].append(segment)
        
        return result