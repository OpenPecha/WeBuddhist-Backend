from uuid import UUID
from typing import List, Dict, Union, Optional
from fastapi import HTTPException
from starlette import status
from .texts_enums import TextType,TextTypes

from pecha_api.error_contants import ErrorConstants
from .texts_repository import (
    check_text_exists, 
    check_all_text_exists, 
    get_texts_by_id, 
    get_texts_by_ids
)
from .texts_response_models import TextDTO
from .texts_response_models import (
    TableOfContent, 
    TextSegment,
    Section,
)
from pecha_api.texts.texts_enums import LANGUAGE_ORDERS

from .groups.groups_service import (
    get_groups_by_list_of_ids
)
from .groups.groups_response_models import GroupDTO
from .texts_repository import get_contents_by_id, get_texts_by_id
from .texts_models import Text
from .texts_cache_service import (
    get_text_details_by_id_cache,
    set_text_details_by_id_cache,
    delete_text_details_by_id_cache
)

from pecha_api.constants import Constants

from pecha_api.cache.cache_enums import CacheType


class TextUtils:
    """
    Utility class for text-related operations.
    Contains helper methods for text processing, validation, and transformations.
    """

    @staticmethod
    async def get_text_details_by_ids(text_ids: List[str]) -> Dict[str, TextDTO]:
        texts_detail = await get_texts_by_ids(text_ids=text_ids)
        return texts_detail
    
    @staticmethod
    async def get_text_details_by_id(text_id: str) -> TextDTO:
        cached_data: TextDTO = await get_text_details_by_id_cache(text_id=text_id, cache_type=CacheType.TEXT_DETAIL)
        if cached_data is not None:
            return cached_data
        
        is_valid_text = await TextUtils.validate_text_exists(text_id=text_id)
        if not is_valid_text:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE)
        text_detail = await get_texts_by_id(text_id=text_id)
        response = TextDTO(
            id=str(text_detail.id),
            pecha_text_id=str(text_detail.pecha_text_id),
            title=text_detail.title,
            language=text_detail.language,
            group_id=text_detail.group_id,
            type=text_detail.type,
            is_published=text_detail.is_published,
            created_date=text_detail.created_date,
            updated_date=text_detail.updated_date,
            published_date=text_detail.published_date,
            published_by=text_detail.published_by,
            categories=text_detail.categories,
            views=text_detail.views,
            source_link=text_detail.source_link,
            ranking=text_detail.ranking,
            license=text_detail.license
        )
        await set_text_details_by_id_cache(text_id=text_id, cache_type=CacheType.TEXT_DETAIL, data=response)
        return response
    
    @staticmethod
    async def validate_text_exists(text_id: str):
        uuid_text_id = UUID(text_id)
        is_exists = await check_text_exists(text_id=uuid_text_id)
        if not is_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE
            )
        return is_exists

    @staticmethod
    async def validate_texts_exist(text_ids: List[str]):
        """
        Validate if multiple texts exist by their IDs.
        
        Args:
            text_ids: List of text IDs to validate
            
        Returns:
            bool: True if all texts exist
            
        Raises:
            HTTPException: If any text does not exist
        """
        uuid_text_ids = [UUID(text_id) for text_id in text_ids]
        all_exists = await check_all_text_exists(text_ids=uuid_text_ids)
        if not all_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE
            )
        return all_exists

    @staticmethod
    def get_all_segment_ids(table_of_content: TableOfContent) -> List[str]:
        """
        Extract all segment IDs from a TableOfContent object.
        
        Args:
            table_of_content: The TableOfContent to extract segment IDs from
            
        Returns:
            List[str]: List of all segment IDs in the table of content
        """
        # Use an iterative approach with a stack
        stack = list(table_of_content.sections)  # Start with top-level sections
        segment_ids = []

        while stack:
            section = stack.pop()

            # Add segment IDs
            segment_ids.extend(
                segment.segment_id
                for segment in section.segments
                if isinstance(segment, TextSegment)
            )

            # Add nested sections to the stack
            if section.sections:
                stack.extend(section.sections)

        return segment_ids
    
    @staticmethod
    async def get_text_detail_by_id(text_id: str) -> TextDTO:
        """
        Get text details by ID.
        
        Args:
            text_id: The ID of the text to retrieve
            
        Returns:
            TextDTO: The text model with details
            
        Raises:
            HTTPException: If the text does not exist or text_id is None
        """
        if text_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ErrorConstants.TEXT_OR_TERM_NOT_FOUND_MESSAGE)
        text = await get_texts_by_id(text_id=text_id)
        if text is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE)
        return TextDTO(
            id=str(text.id),
            pecha_text_id=str(text.pecha_text_id),
            title=text.title,
            language=text.language,
            group_id=text.group_id,
            type=text.type,
            is_published=text.is_published,
            created_date=text.created_date,
            updated_date=text.updated_date,
            published_date=text.published_date,
            published_by=text.published_by,
            categories=text.categories,
            views=text.views,
            source_link=text.source_link,
            ranking=text.ranking,
            license=text.license
        )
        

    @staticmethod
    async def get_table_of_content_id_and_respective_section_by_segment_id(text_id: str, segment_id: str) -> Optional[TableOfContent]:
        """
        Searches for a segment_id within all sections of table of contents for the given text_id.
        Returns a TableOfContent object with only the section containing the segment_id.
        
        Args:
            text_id: The ID of the text to search in
            segment_id: The ID of the segment to search for
            
        Returns:
            TableOfContent: A TableOfContent object with only the section containing the segment_id,
                           or None if the segment is not found
        """
        table_of_contents = await get_contents_by_id(text_id=text_id)

        # Search through all table of contents
        for content in table_of_contents:
            found_section = _find_section_with_segment(getattr(content, "sections", []), segment_id)
            if found_section:
                # Create a new TableOfContent with only the found section
                filtered_content = TableOfContent(
                    id=str(content.id),
                    text_id=content.text_id,
                    type=content.type,
                    sections=[found_section]  # Only include the section with the segment_id
                )
                return filtered_content
                
        return None  # Return None if segment not found in any section

    @staticmethod
    def get_language_priority(text_language: Optional[str], preferred_language: str) -> int:
        order = LANGUAGE_ORDERS.get(preferred_language)
        return order.get(text_language, 999)

    @staticmethod
    def filter_text_on_root_and_version(texts: List[TextDTO], language: str) -> Dict[str, Union[TextDTO, List[TextDTO]]]:
        filtered_text = {
            TextType.ROOT_TEXT.value: None,
            TextTypes.VERSIONS.value: []
        }
        versions = []
        for text in texts:
            if str(text.id) in Constants.excluded_text_ids:
                continue
            text_type_value = text.type if isinstance(text.type, str) else text.type.value
            # if text.language == language and filtered_text[TextType.ROOT_TEXT.value] is None:
            #     filtered_text[TextType.ROOT_TEXT.value] = text
            if text.language == language and filtered_text[TextType.ROOT_TEXT.value] is None:
                filtered_text[TextType.ROOT_TEXT.value] = text
            else:
                versions.append(text)
            
        filtered_text[TextTypes.VERSIONS.value] = versions

        if filtered_text[TextType.ROOT_TEXT.value] is None and (len(versions) > 0):
            for text in versions:
                versions.sort(
                    key=lambda text: TextUtils.get_language_priority(text.language, language)
                )
            filtered_text[TextType.ROOT_TEXT.value] = versions[0]
            # Remove the promoted version from the versions list
            filtered_text[TextTypes.VERSIONS.value] = versions[1:]


        return filtered_text
    
    @staticmethod
    async def filter_text_base_on_group_id_type(texts: List[TextDTO], language: str) -> Dict[str, Union[TextDTO, List[TextDTO]]]:
        filtere_text = {
            TextType.ROOT_TEXT.value: None,
            TextType.COMMENTARY.value: []
        }
        if texts:
            group_ids = [text.group_id for text in texts]
            group_ids_type_dict: Dict[str, GroupDTO] = await get_groups_by_list_of_ids(group_ids=group_ids)

            commentary = []
            for text in texts:
                # remove duplicate text
                if str(text.id) in Constants.excluded_text_ids:
                    continue
                if (group_ids_type_dict.get(text.group_id).type == "text") and (text.language == language) and filtere_text[TextType.ROOT_TEXT.value] is None:
                    filtere_text[TextType.ROOT_TEXT.value] = text
                elif (group_ids_type_dict.get(text.group_id).type == TextType.COMMENTARY.value and text.language == language):
                    commentary.append(text)
            filtere_text[TextType.COMMENTARY.value] = commentary
        return filtere_text

    @staticmethod
    async def filter_text_base_on_group_id_type_and_language_preference(texts: List[TextDTO], language: str) -> Dict[str, Union[TextDTO, List[TextDTO]]]:
        filtere_text = {
            TextType.ROOT_TEXT.value: None,
            TextType.COMMENTARY.value: []
        }
        if texts:
            group_ids = [text.group_id for text in texts]
            group_ids_type_dict: Dict[str, GroupDTO] = await get_groups_by_list_of_ids(group_ids=group_ids)
    
            commentary = []
            for text in texts:
                # remove duplicate text
                if str(text.id) in Constants.excluded_text_ids:
                    continue
                
                # Since texts are already sorted by language preference,
                # just pick the first one that matches the type
                if (group_ids_type_dict.get(text.group_id).type == "text") and filtere_text[TextType.ROOT_TEXT.value] is None:
                    filtere_text[TextType.ROOT_TEXT.value] = text
                elif (group_ids_type_dict.get(text.group_id).type == TextType.COMMENTARY.value and text.language == language):
                    commentary.append(text)
            filtere_text[TextType.COMMENTARY.value] = commentary
        return filtere_text

    @staticmethod
    async def get_commentaries_by_text_type(text_type: str, language: str, skip: int, limit: int) -> List[TextDTO]:
        texts = await Text.find({"type": "commentary"}).to_list()
    
        return [
            TextDTO(
                id=str(text.id),
                pecha_text_id=str(text.pecha_text_id) if text.pecha_text_id else None,
                title=text.title,
                language=text.language,
                group_id=text.group_id,
                type=text.type,
                is_published=text.is_published,
                created_date=text.created_date,
                updated_date=text.updated_date,
                published_date=text.published_date,
                published_by=text.published_by,
                categories=text.categories,
                views=text.views,
                source_link=text.source_link,
                ranking=text.ranking,
                license=text.license
            )
            for text in texts
        ]
        
    

def _find_section_with_segment(sections, segment_id: str):
    """
    Recursive function to search for segment_id in sections.
    
    Args:
        sections: List of sections to search through
        segment_id: The ID of the segment to search for
        
    Returns:
        Section: The section containing the segment_id, or None if not found
    """
    for section in sections:
        # Check if segment_id exists in this section's segments
        for segment in getattr(section, "segments", []):
            if getattr(segment, "segment_id", None) == segment_id:
                return section
                
        # Check subsections recursively
        if getattr(section, "sections", None):
            found_section = _find_section_with_segment(section.sections, segment_id)
            if found_section:
                # we need to return the outermost section and not the inner most section
                return section
    return None