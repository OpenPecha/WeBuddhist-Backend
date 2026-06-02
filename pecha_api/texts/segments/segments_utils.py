from typing import Dict, List, Optional, Union
from uuid import UUID
from fastapi import HTTPException
from starlette import status

from pecha_api.error_contants import ErrorConstants
from pecha_api.texts.texts_enums import TextType
from .segments_response_models import MappedSegmentDTO, MappedSegmentResponseDTO, SegmentDTO, SegmentCommentry, SegmentTranslation, SegmentTransliteration, SegmentAdaptation, SegmentRootMapping, SegmentRecitation
from .segments_repository import (
    check_segment_exists,
    check_all_segment_exists,
    get_segment_by_id,
    get_related_mapped_segments,
)
from ..texts_response_models import TextDTO
from ..texts_repository import get_contents_by_id
from pecha_api.constants import Constants


from ..groups.groups_service import (
    get_group_details
)
from ..texts_utils import TextUtils
from ..texts_response_models import (
    DetailTableOfContent,
    DetailSection,
    DetailTextSegment,
    TableOfContent,
    Translation,
)
from .segments_response_models import (
    SegmentCommentry,
    SegmentTranslation,
    SegmentTransliteration,
    SegmentAdaptation,
    SegmentRootMapping,
    SegmentRecitation
)

def _extract_segment_order(section, segment_order_map: Dict[str, int]):

    if section is None:
        return
    
    if section.segments:
        for segment in section.segments:
            if segment.segment_id:
                segment_order_map[segment.segment_id] = segment.segment_number
    
    if section.sections:
        for subsection in section.sections:
            _extract_segment_order(subsection, segment_order_map)


class SegmentUtils:
    """
    Utility class for segment-related operations.
    """
    
    @staticmethod
    async def validate_segment_exists(segment_id: str) -> bool:
        """Validate that a segment exists."""
        try:
            uuid_segment_id = UUID(segment_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid segment ID format: {str(e)}. Segment ID must be a valid UUID."
            )
        is_exists = await check_segment_exists(segment_id=uuid_segment_id)
        if not is_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE,
            )
        return is_exists
    
    @staticmethod
    async def validate_segments_exists(segment_ids: List[str]) -> bool:
        """Validate that all segment IDs in the list exist."""
        try:
            uuid_segment_ids = [UUID(segment_id) for segment_id in segment_ids]
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid segment ID format: {str(e)}. All segment IDs must be valid UUIDs."
            )
        all_exists = await check_all_segment_exists(segment_ids=uuid_segment_ids)
        if not all_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE} {segment_ids}",
            )
        return all_exists
    
        
    @staticmethod
    async def get_count_of_each_commentary_and_version(
        segments: List[SegmentDTO],
        parent_text: TextDTO
    ) -> Dict[str, int]:
        """
        Count the number of commentary and version segments in the provided list.
        """
        count = {"commentary": 0, "version": 0}
        unique_text_ids = set()
        text_ids = [segment.text_id for segment in segments]
        text_details_dict = await TextUtils.get_text_details_by_ids(text_ids=text_ids)
        for segment in segments:
            text_id = segment.text_id
            if text_id in unique_text_ids:
                continue
            unique_text_ids.add(text_id)
            text_detail = text_details_dict.get(text_id)
            if text_detail and text_detail.type == "commentary":
                count["commentary"] += 1
            elif text_detail and text_detail.type == "version" and text_detail.type == parent_text.type:
                count["version"] += 1
        return count

    @staticmethod
    async def filter_segment_mapping_by_type_or_text_id(
        segments: List[SegmentDTO], type: str, text_id: Optional[str] = None
    ) -> List[Union[SegmentCommentry, SegmentTranslation, SegmentTransliteration, SegmentAdaptation]]:
        """
        Filter segment mappings by type and optionally by text_id.
        """
        text_ids = [segment.text_id for segment in segments]
        text_details_dict = await TextUtils.get_text_details_by_ids(text_ids=text_ids)
        
        grouped_segments = await SegmentUtils._group_segment_content_by_text_id(segments=segments)
        filtered_segments = []
        appended_commentary_text_ids = []
        for segment in segments:
            text_detail = text_details_dict.get(segment.text_id)
            
            if not text_detail:
                continue

            if str(text_detail.id) in Constants.excluded_text_ids:
                continue

            elif text_detail.type == TextType.VERSION.value and type == TextType.VERSION.value:
                if text_id is not None and text_id != segment.text_id:
                    continue

                filtered_segments.append(
                    SegmentTranslation(
                        segment_id=str(segment.id),
                        text_id=segment.text_id,
                        title=text_detail.title,
                        source=text_detail.published_by,
                        language=text_detail.language,
                        content=segment.content
                    )
                )
            elif text_detail.type == TextType.COMMENTARY.value and type == TextType.COMMENTARY.value:
                if text_id is not None and text_id != segment.text_id:
                    continue
                if segment.text_id in appended_commentary_text_ids:
                    continue
                grouped = grouped_segments.get(segment.text_id, [])
                if grouped:
                    merged_content = "".join([seg.content for seg in grouped])
                    mapped_segments = [
                        MappedSegmentDTO(
                            segment_id=str(grouped[0].id),
                            content=merged_content
                        )
                    ]
                else:
                    mapped_segments = []
                count = len(mapped_segments)
                filtered_segments.append(
                    SegmentCommentry(
                        text_id=segment.text_id,
                        title=text_detail.title,
                        segments=mapped_segments,
                        language=text_detail.language,
                        count=count
                    )
                )
                appended_commentary_text_ids.append(segment.text_id)
                
        return filtered_segments
    
    @staticmethod
    async def get_root_mapping_count(segment_id: str) -> int:
        segment = await get_segment_by_id(segment_id=segment_id)
        text_id = segment.text_id
        text_detail = await TextUtils.get_text_details_by_id(text_id=text_id)
        group_id = text_detail.group_id
        group_detail = await get_group_details(group_id=group_id)
        if group_detail.type == "text":
            return 0
        root_mapping_count = 0
        for mapping in segment.mapping:
            text_detail = await TextUtils.get_text_details_by_id(text_id=mapping.text_id)
            if text_detail.type == "commentary":
                continue
            root_mapping_count += 1
        return root_mapping_count

    @staticmethod
    async def get_mapped_segment_content_for_table_of_content(
        table_of_content: TableOfContent, version_id: Optional[str]
    ) -> DetailTableOfContent:
        """
        Convert a TableOfContent model to a DetailTableOfContent model by enriching
        each segment with detailed information fetched from get_segment_details_by_id.
        
        Args:
            table_of_content: The TableOfContent model to be converted
            
        Returns:
            A DetailTableOfContent model with enriched segment details
        """
        
        # Create a new DetailTableOfContent with the same base attributes
        detail_table_of_content = DetailTableOfContent(
            id=str(table_of_content.id) if table_of_content.id else None,
            text_id=table_of_content.text_id,
            sections=[]
        )
        
        async def process_section(section) -> DetailSection:
            detail_section = DetailSection(
                id=section.id,
                title=section.title,
                section_number=section.section_number,
                parent_id=section.parent_id,
                segments=[],
                sections=[],
                created_date=section.created_date,
                updated_date=section.updated_date,
                published_date=section.published_date,
            )
            # Process segments
            for segment in section.segments:
                segment_details = await get_segment_by_id(segment_id=segment.segment_id)
                translation = None
                if version_id is not None:
                    version_text_detail = await TextUtils.get_text_details_by_id(text_id=version_id)
                    segments = await get_related_mapped_segments(parent_segment_id=segment.segment_id)
                    filtered_translation_by_version_id = await SegmentUtils.filter_segment_mapping_by_type_or_text_id(
                        segments=segments,
                        type=TextType.VERSION.value,
                        text_id=version_id #pass the version_id so that only the mapping with a particular text_id is selected
                    )
                    if filtered_translation_by_version_id:
                        translation = Translation(
                            text_id=filtered_translation_by_version_id[0].text_id,
                            language=version_text_detail.language,
                            content=filtered_translation_by_version_id[0].content
                        )
                # Create DetailTextSegment with enriched information
                detail_segment = DetailTextSegment(
                    segment_id=segment.segment_id,
                    segment_number=segment.segment_number,
                    content=segment_details.content,
                    translation=translation
                )
                
                detail_section.segments.append(detail_segment)
            
            # Process nested sections recursively
            if section.sections:
                for subsection in section.sections:
                    detail_subsection = await process_section(subsection)
                    detail_section.sections.append(detail_subsection)
            
            return detail_section
        
        # Process all top-level sections
        for section in table_of_content.sections:
            detail_section = await process_section(section)
            detail_table_of_content.sections.append(detail_section)
        
        return detail_table_of_content
    
    @staticmethod
    async def get_segment_root_mapping_details(segments: List[SegmentDTO], parent_segment_text: TextDTO) -> List[SegmentRootMapping]:
        list_of_text_ids = [
            segment.text_id
            for segment in segments
        ]
        texts_dict = await TextUtils.get_text_details_by_ids(text_ids=list_of_text_ids)
        grouped_segments = await SegmentUtils._group_segment_content_by_text_id(segments=segments)
        list_of_segment_root_mapping = []
        appended_text_ids = []
        
        for segment in segments:
            text_detail = texts_dict.get(segment.text_id)
            if text_detail:
                if segment.text_id in appended_text_ids:
                    continue
                mapped_segments = []
                for segment_item in grouped_segments.get(segment.text_id, []):
                    mapped_segments.append(MappedSegmentResponseDTO(
                        segment_id=str(segment_item.id),
                        content=segment_item.content,
                        language=text_detail.language
                    ))
                if text_detail.type == parent_segment_text.type:
                    continue
                list_of_segment_root_mapping.append(
                    SegmentRootMapping(
                        text_id=segment.text_id,
                        title=text_detail.title,
                        language=text_detail.language,
                        segments=mapped_segments
                    )
                )
                appended_text_ids.append(segment.text_id)
        return list_of_segment_root_mapping

    @staticmethod
    async def _group_segment_content_by_text_id(segments: List[SegmentDTO]) -> Dict[str, List[SegmentDTO]]:
        grouped_segments = {}
        for segment in segments:
            if segment.text_id not in grouped_segments:
                grouped_segments[segment.text_id] = []
            grouped_segments[segment.text_id].append(segment)
        
        for text_id, segment_list in grouped_segments.items():
            try:
                table_of_contents = await get_contents_by_id(text_id=text_id)
                
                segment_order_map = {}
                for toc in table_of_contents:
                    for section in toc.sections:
                        _extract_segment_order(section, segment_order_map)
                
                segment_list.sort(key=lambda s, order_map=segment_order_map: order_map.get(str(s.id), float('inf')))
                
            except Exception:
                segment_list.sort(key=lambda s: s.pecha_segment_id or "")
        
        return grouped_segments
    
