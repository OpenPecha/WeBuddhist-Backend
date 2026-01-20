import uuid
from uuid import UUID
from typing import List, Optional

from .texts_response_models import Section

from pydantic import Field
from beanie import Document

from pecha_api.sheets.sheets_enum import (
    SortBy, 
    SortOrder
)

from .texts_enums import TextType
from .texts_response_models import TextDTO, TableOfContentType

class TableOfContent(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    text_id: str
    type: Optional[TableOfContentType] = None
    sections: List[Section]

    class Settings:
        collection = "table_of_contents"
    
    @classmethod
    async def get_table_of_contents_by_text_id(cls, text_id: str) -> List["TableOfContent"]: # this methods is getting all the available table of content for a text
        query = cls.find(cls.text_id == text_id)
        return await query.to_list()

    @classmethod
    async def delete_table_of_content_by_text_id(cls, text_id: str):
        return await cls.find(cls.text_id == text_id).delete()
    
    @classmethod
    async def get_sections_count(cls, content_id: str) -> int:
        table_of_content = await cls.find_one(cls.id == UUID(content_id))
        if table_of_content and hasattr(table_of_content, "sections"):
            return len(table_of_content.sections)
        return 0
    
    @classmethod
    async def get_table_of_content_by_content_id(cls, content_id: str, skip: int = None, limit: int = None) -> Optional["TableOfContent"]:
        contents = await cls.find_one(cls.id == UUID(content_id))
        if contents and skip is not None and limit is not None:
            contents.sections.sort(key=lambda section: section.section_number)
            if (skip * limit) > len(contents.sections):
                return None
            contents.sections = contents.sections[skip * limit:skip+limit]
        return contents


class Text(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    pecha_text_id: Optional[str] = None
    title: str
    language: Optional[str] = None
    group_id: str
    is_published: bool
    created_date: str
    updated_date: str
    published_date: str
    published_by: str
    source_link:Optional[str] = None
    ranking:Optional[int] = None
    license:Optional[str] = None
    type: TextType
    categories: Optional[List[str]] = None
    views: Optional[int] = 0
    likes: Optional[List[str]] = []

    class Settings:
        collection = "texts"

    @classmethod
    async def get_texts_by_pecha_text_ids(cls, pecha_text_ids: List[str]) -> List["Text"]:
        return await cls.find({cls.pecha_text_id: {"$in": pecha_text_ids}}).to_list()

    @classmethod
    async def get_text_by_pecha_text_id(cls, pecha_text_id: str) -> Optional["Text"]:
        return await cls.find_one(cls.pecha_text_id == pecha_text_id)   
    @classmethod
    async def get_text(cls, text_id: str) -> Optional["Text"]:
        try:
            text_uuid = UUID(text_id)
        except ValueError:
            return None
        return await cls.find_one(cls.id == text_uuid)
    
    
    @classmethod
    async def get_texts_by_ids(cls, text_ids: List[str]) -> List["Text"]:
        # Filter out non-UUID text_ids
        valid_text_uuids = []
        for text_id in text_ids:
            try:
                if text_id is not None:
                    valid_text_uuids.append(UUID(text_id))
            except ValueError:
                # Skip invalid UUIDs
                continue
                
        if not valid_text_uuids:
            return []
            
        return await cls.find({"_id": {"$in": valid_text_uuids}}).to_list()

    @classmethod
    async def check_exists(cls, text_id: uuid.UUID) -> bool:
        text = await cls.find_one(cls.id == text_id)
        return text is not None  # True if exists, False otherwise

    @classmethod
    async def exists_all(cls, text_ids: List[UUID], batch_size: int = 100) -> bool:
        for i in range(0, len(text_ids), batch_size):
            batch_ids = text_ids[i: i + batch_size]
            found_texts = await cls.find({"_id": {"$in": batch_ids}}).to_list()

            found_ids = {text.id for text in found_texts}

            # If any ID from the current batch is missing, stop early
            if len(found_ids) < len(batch_ids):
                return False  # One or more IDs are missing
        return True  # All IDs exist
    
    # @classmethod
    # async def get_texts_by_collection_id(cls, collection_id: str, language: str, skip: int, limit: int) -> List["Text"]:
    #     query = {
    #         "categories": collection_id,
    #         "language": language
    #     }
    #     texts = (
    #         await cls.find(
    #             query
    #         )
    #         .skip(skip)
    #         .limit(limit)
    #         .to_list()
    #     )
    #     return texts

    @classmethod
    async def get_texts_by_collection_id(cls, collection_id: str, skip: int, limit: int, language: str | None = None) -> List["Text"]:
        query = {
            "categories": collection_id
        }
        if language is not None:
            query["language"] = language
        texts = (
            await cls.find(
                query
            )
            .skip(skip)
            .limit(limit)
            .to_list()
        )
        return texts

    @classmethod
    async def get_all_texts_by_collection_id(cls, collection_id):
        
        query = {
            "categories": collection_id
        }
        return await cls.find(
            query
        ).to_list()

    @classmethod
    async def get_all_recitation_texts_by_collection_id(cls, collection_id: str, language: str):
        
        query = {
            "categories": collection_id,
            "language": language
        }
        return await cls.find(
            query
        ).to_list()

    @classmethod
    async def get_texts_by_group_id(cls, group_id: str, skip: int, limit: int) -> List["Text"]:
        query = {
            "group_id": group_id
        }
        texts = (
            await cls.find(query)
            .skip(skip)
            .limit(limit)
            .to_list()
        )
        return texts
    
    @classmethod
    async def get_all_texts_by_group_id(cls, group_id: str) -> List["Text"]:
        query = {
            "group_id": group_id
        }
        texts = (
            await cls.find(query)
            .to_list()
        )
        return texts

    @classmethod
    async def update_text_details_by_id(cls, text_id: UUID, text_details: TextDTO):
        return await cls.update_all(cls.id == text_id, {"$set": text_details.model_dump()})
    
    @classmethod
    async def delete_text_by_id(cls, text_id: UUID):
        return await cls.find_one(cls.id == text_id).delete()


    @classmethod
    async def get_sheets(
        cls, 
        published_by: Optional[str] = None,
        is_published: Optional[bool] = None,
        sort_by: Optional[SortBy] = None,
        sort_order: Optional[SortOrder] = None,
        skip: int = 0, 
        limit: int = 10
    ) -> List["Text"]:
        query = {"type": TextType.SHEET}
            
        if published_by is not None:
            query["published_by"] = published_by
            
        if is_published is not None:
            query["is_published"] = is_published

        mongo_query = cls.find(query)
        if sort_by:
            field = {
                SortBy.CREATED_DATE: "created_date",
                SortBy.PUBLISHED_DATE: "published_date",
            }
            sort_field = field.get(sort_by)
            if sort_field:
                if sort_order == SortOrder.DESC:
                    sort_string = f"-{sort_field}"
                else:
                    sort_string = sort_field
            
                mongo_query = mongo_query.sort(sort_string)

        mongo_query = mongo_query.skip(skip).limit(limit)


        texts = await mongo_query.to_list()

        return texts


    @classmethod
    async def get_published_sheets_count_from_db(
        cls,
        email: Optional[str] = None
    ) -> int:
        query = {
            "type": TextType.SHEET, 
            "is_published": True
        }
        if email is not None:
            query["published_by"] = email
        return await cls.find(query).count()
